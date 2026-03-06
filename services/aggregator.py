import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from scrapers.idealista import IdealistaScraper
from scrapers.imovirtual import ImovirtualScraper
from scrapers.supercasa import SupercasaScraper
from scrapers.casasapo import CasaSapoScraper
from scrapers.remax import RemaxScraper
from scrapers.olx import OLXScraper
from scrapers.utils import slugify_pt
from services.db import save_listings, get_listings_from_db, update_daily_stats
from services.processor import apply_filters, clean_data, apply_sort, calculate_stats, apply_sources, DISTRICTS
from services.property_matcher import normalize_typology, match_property_typology

from cachetools import TTLCache

logger = logging.getLogger("aggregator")

SCRAPERS = {
    "idealista": IdealistaScraper(),
    "imovirtual": ImovirtualScraper(),
    "supercasa": SupercasaScraper(),
    "casasapo": CasaSapoScraper(),
    "remax": RemaxScraper(),
    "olx": OLXScraper(),
}

CACHE = TTLCache(maxsize=256, ttl=600)  # Query result cache (10 min)

def get_listings(district, pages, sources, filters, sort, limit, typology, search_type="rent"):
    if district not in DISTRICTS:
        district = "Leiria"

    district_slug = slugify_pt(district)
    sources = [s for s in sources if s in SCRAPERS]
    norm_typology = normalize_typology(typology)

    cache_key = (district, district_slug, pages, tuple(sorted(sources)), norm_typology, search_type, limit)
    if cache_key in CACHE:
        items = CACHE[cache_key]
    else:
        # 1. Try search on the database first
        db_items = get_listings_from_db(district, search_type, norm_typology, limit=limit)
        
        if len(db_items) >= limit:
            logger.info(f"Found sufficient results ({len(db_items)}) in DB for {district} ({search_type}, {typology})")
            items = db_items
        else:
            if db_items:
                logger.info(f"Found {len(db_items)} results in DB, but need {limit}. Scraping for more...")
            else:
                logger.info(f"No results in DB for {district} ({search_type}, {typology}). Scraping...")

            # 2. Scrape if not enough data in DB
            scraped_items = []
            with ThreadPoolExecutor(max_workers=min(8, len(sources) or 1)) as ex:
                futs = []
                for s in sources:
                    futs.append(ex.submit(SCRAPERS[s].scrape, district, district_slug, pages, typology, search_type))
                for f in as_completed(futs):
                    try:
                        res = f.result()
                        for item in res:
                            item['search_type'] = search_type
                        scraped_items.extend(res)
                    except Exception as e:
                        logger.error(f"Scraper failed with exception: {e}")

            # dedupe por URL
            seen = {x['url'] for x in db_items if 'url' in x}
            new_items = []
            for x in scraped_items:
                u = x.get("url")
                if not u or u in seen:
                    continue
                seen.add(u)
                new_items.append(x)

            # 3. Clean and Save new items
            if new_items:
                cleaned_new = clean_data(new_items, district=district, search_type=search_type)
                logger.info(f"Saving {len(cleaned_new)} new listings to DB (out of {len(new_items)} scraped)")
                save_listings(cleaned_new, search_type, norm_typology)
                update_daily_stats()
            
            # 4. Final collection
            items = get_listings_from_db(district, search_type, norm_typology, limit=limit)
            CACHE[cache_key] = items

    # 5. Apply transient filters, typology matching (if generic search), source filtering and sorting
    filtered = apply_sources(items, sources)
    filtered = match_property_typology(filtered, typology)
    filtered = apply_filters(filtered, filters)
    sorted_items = apply_sort(filtered, sort)
    
    # 6. Stats of what is VISIBLE
    stats = calculate_stats(sorted_items)
    return sorted_items, stats

def bulk_scrape(pages_per_query=1):
    """Run a comprehensive scrape for all districts and typical typologies."""
    logger.info("Starting bulk scrape for all districts...")
    sources = list(SCRAPERS.keys())
    typologies = ["T1", "T2", "T3"]
    search_types = ["rent", "buy"]
    
    for district in DISTRICTS:
        for st in search_types:
            for ty in typologies:
                try:
                    logger.info(f"Bulk scraping: {district} | {st} | {ty}")
                    # side effect of saving to DB
                    get_listings(
                        district=district,
                        pages=pages_per_query,
                        sources=sources,
                        filters={},
                        sort="eur_m2_asc",
                        limit=50, 
                        typology=ty,
                        search_type=st
                    )
                    time.sleep(1) # Small gap between major queries
                except Exception as e:
                    logger.error(f"Error in bulk scrape for {district}/{st}/{ty}: {e}")
    
    logger.info("Bulk scrape finished.")

def run_maintenance():
    """Maintenance task: fix district mismatches and check URL activity"""
    logger.info("Running maintenance: checking all listings for district mismatches and activity...")
    from services.db import DB_PATH
    import sqlite3
    import requests
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT url, district, title, snippet FROM listings WHERE is_active = 1")
    rows = cur.fetchall()
    
    wrong_count = 0
    deactivated_count = 0
    
    # Simple activity check: only for a sample or all? Let's do a basic HEAD request.
    # To avoid being too slow, we could skip this or do it in parallel.
    # The user said "label the listing has active or not based on the url, that is true maintenence"
    
    for url, current_district, title, snippet in rows:
        # 1. District Mismatch Check
        expected_slug = slugify_pt(current_district).replace("-", " ")
        url_lower = url.lower()
        text_normalized = slugify_pt((title or "") + " " + (snippet or "")).lower().replace("-", " ")
        
        found_other = None
        if expected_slug.replace(" ", "-") not in url_lower and expected_slug not in text_normalized:
            for d in DISTRICTS:
                if d == current_district: continue
                d_slug = slugify_pt(d).replace("-", " ")
                if d_slug in text_normalized:
                    found_other = d
                    break
            
            if found_other:
                cur.execute("UPDATE listings SET district = ? WHERE url = ?", (found_other, url))
                wrong_count += 1

        # 2. Activity Check (Head request)
        # We only do this if it wasn't just updated
        try:
            # Short timeout, we don't want to hang
            resp = requests.head(url, timeout=5, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 404:
                cur.execute("UPDATE listings SET is_active = 0 WHERE url = ?", (url,))
                deactivated_count += 1
        except:
            # If we can't reach it, we don't necessarily deactivate it immediately
            # maybe it's a temporary network issue. 
            pass
                
    if wrong_count > 0 or deactivated_count > 0:
        logger.info(f"Maintenance: Fixed {wrong_count} district mismatches and deactivated {deactivated_count} dead listings.")
        conn.commit()
    else:
        logger.info("Maintenance: No changes needed.")
    
    conn.close()
