import time
import statistics
import re
import logging
from cachetools import TTLCache, LRUCache
from concurrent.futures import ThreadPoolExecutor, as_completed

from scrapers.idealista import IdealistaScraper
from scrapers.imovirtual import ImovirtualScraper
from scrapers.supercasa import SupercasaScraper
from scrapers.casasapo import CasaSapoScraper
from scrapers.remax import RemaxScraper
from scrapers.olx import OLXScraper
from scrapers.utils import slugify_pt, parse_typology
from services.database import save_listings, get_listings_from_db, update_daily_stats

DISTRICTS = [
    "Aveiro", "Beja", "Braga", "Bragança", "Castelo Branco", "Coimbra", "Évora",
    "Faro", "Guarda", "Leiria", "Lisboa", "Portalegre", "Porto", "Santarém",
    "Setúbal", "Viana do Castelo", "Vila Real", "Viseu"
]

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
LISTINGS_CACHE = LRUCache(maxsize=2000) # Last 2000 individual listings cache

def _apply_filters(items, filters):
    out = []
    for x in items:
        p = x.get("price_eur")
        a = x.get("area_m2")
        e = x.get("eur_m2")

        if filters.get("min_price") is not None and (p is None or p < filters["min_price"]):
            continue
        if filters.get("max_price") is not None and (p is None or p > filters["max_price"]):
            continue
        if filters.get("min_area") is not None and (a is None or a < filters["min_area"]):
            continue
        if filters.get("max_area") is not None and (a is None or a > filters["max_area"]):
            continue
        if filters.get("only_with_eurm2") and e is None:
            continue

        if filters.get("exclude_temporary", True):
            title = x.get("title") or ""
            snippet = x.get("snippet") or ""
            txt = (title + " " + snippet).lower()
            # heurística simples (podes acrescentar palavras)
            if "temporário" in txt or "temporario" in txt or "subloc" in txt or "até " in txt or "ate " in txt:
                continue

        out.append(x)
    return out

def _sort(items, sort):
    def key_eurm2(x):
        v = x.get("eur_m2")
        return (v is None, v if v is not None else 10**18)

    def key_price(x):
        v = x.get("price_eur")
        return (v is None, v if v is not None else 10**18)

    if sort == "eur_m2_desc":
        return sorted(items, key=key_eurm2, reverse=True)
    if sort == "price_asc":
        return sorted(items, key=key_price)
    if sort == "price_desc":
        return sorted(items, key=key_price, reverse=True)
    # default: eur_m2_asc
    return sorted(items, key=key_eurm2)

def _stats(items):
    by_source = {}
    eurm2_vals = []
    for x in items:
        by_source.setdefault(x["source"], 0)
        by_source[x["source"]] += 1
        if x.get("eur_m2") is not None:
            eurm2_vals.append(x["eur_m2"])

    med = statistics.median(eurm2_vals) if eurm2_vals else None
    return {
        "count": len(items),
        "by_source": by_source,
        "median_eur_m2": med
    }

def _normalize_typology(t: str) -> str:
    if not t:
        return "T2"
    t = t.strip().upper().replace(" ", "")
    if t in {"*", "ALL", "T*"}:
        return "T*"
    if not t.startswith("T"):
        t = "T" + t
    return t


def _typology_regex(t: str):
    t = _normalize_typology(t)
    if t == "T*":
        return None
    # Build a regex that matches e.g., T2 or T2+1 with optional spaces
    plus_idx = t.find("+")
    if plus_idx != -1:
        base = re.escape(t[1:plus_idx])  # digits after T
        extra = re.escape(t[plus_idx+1:])
        pat = rf"\bT\s*{base}\s*\+\s*{extra}\b"
    else:
        base = re.escape(t[1:])
        # Do not match T2+1 when filtering T2 (negative lookahead for '+')
        pat = rf"\bT\s*{base}(?!\s*\+)\b"
    return re.compile(pat, re.IGNORECASE)


def _apply_typology(items, typology):
    rx = _typology_regex(typology)
    if rx is None:
        return items
    out = []
    for x in items:
        title = x.get("title") or ""
        snippet = x.get("snippet") or ""
        txt = (title + " " + snippet).strip()
        if rx.search(txt):
            out.append(x)
    return out


def _apply_sources(items, sources):
    if not sources:
        return items
    return [x for x in items if x.get("source") in sources]

def get_listings(district, pages, sources, filters, sort, limit, typology, search_type="rent"):
    if district not in DISTRICTS:
        district = "Leiria"

    district_slug = slugify_pt(district)
    sources = [s for s in sources if s in SCRAPERS]
    norm_typology = _normalize_typology(typology)

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
            # concorrência por fonte (cada scraper faz as páginas por ordem com pausas leves)
            with ThreadPoolExecutor(max_workers=min(8, len(sources) or 1)) as ex:
                futs = []
                for s in sources:
                    futs.append(ex.submit(SCRAPERS[s].scrape, district, district_slug, pages, typology, search_type))
                for f in as_completed(futs):
                    try:
                        res = f.result()
                        logger.info(f"Scraper finished. Got {len(res)} results.")
                        for item in res:
                            item['search_type'] = search_type
                        scraped_items.extend(res)
                    except Exception as e:
                        # não aborta tudo se uma fonte falhar
                        logger.error(f"Scraper failed with exception: {e}")
                        pass

            # dedupe por URL
            seen = {x['url'] for x in db_items if 'url' in x}
            new_items = []
            for x in scraped_items:
                u = x.get("url")
                if not u or u in seen:
                    continue
                seen.add(u)
                new_items.append(x)
            
            # Save results to database (handles new items and updates)
            if scraped_items:
                # Ensure each item has a typology, fallback to title/snippet extraction or query typology
                for item in scraped_items:
                    if not item.get("typology"):
                        extracted = parse_typology((item.get("title") or "") + " " + (item.get("snippet") or ""))
                        if extracted:
                            item["typology"] = extracted
                        else:
                            item["typology"] = norm_typology
                    # Normalize whatever we have
                    if item.get("typology"):
                        item["typology"] = _normalize_typology(item["typology"])

                try:
                    save_listings(scraped_items, search_type, norm_typology)
                    update_daily_stats()
                except Exception as e:
                    logger.error(f"Failed to save listings to DB: {e}")

            # Combine DB and Scraped
            items = db_items + new_items

        # Populate 2k entries cache
        for item in items:
            if 'url' in item:
                LISTINGS_CACHE[item['url']] = item

        CACHE[cache_key] = items

    # Filtro adicional por tipologia (por segurança), sobretudo útil quando uma fonte não suporta o filtro via URL
    items = _apply_sources(items, sources)
    items = _apply_typology(items, typology)

    items = _apply_filters(items, filters)
    items = _sort(items, sort)
    items = items[:limit]
    return items, _stats(items)
