import statistics
import logging
from scrapers.utils import slugify_pt

logger = logging.getLogger("processor")

DISTRICTS = [
    "Algarve", "Aveiro", "Beja", "Braga", "Bragança", "Castelo Branco", "Coimbra", "Évora",
    "Faro", "Guarda", "Leiria", "Lisboa", "Portalegre", "Porto", "Santarém",
    "Setúbal", "Viana do Castelo", "Vila Real", "Viseu"
]

def apply_filters(items, filters):
    """Filters data based on price, area, and keywords"""
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
            if "temporário" in txt or "temporario" in txt or "subloc" in txt or "até " in txt or "ate " in txt:
                continue

        out.append(x)
    return out

def clean_data(items, district=None, search_type="rent"):
    """Removes junk data (zero values)"""
    out = []
    
    for x in items:
        p = x.get("price_eur")
        a = x.get("area_m2")
        
        # Only discard truly invalid items with missing or zero price/area
        if p is None or p <= 0 or a is None or a <= 0:
            continue
            
        out.append(x)
    return out

def apply_sort(items, sort):
    """Sorts data by price or eur_m2"""
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
    return sorted(items, key=key_eurm2)

def calculate_stats(items):
    """Generates statistics from data"""
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

def apply_sources(items, sources):
    """Filters data based on selected sources"""
    if not sources:
        return items
    return [x for x in items if x.get("source") in sources]
