import time
import statistics
import re
from cachetools import TTLCache
from concurrent.futures import ThreadPoolExecutor, as_completed

from scrapers.idealista import IdealistaScraper
from scrapers.imovirtual import ImovirtualScraper
from scrapers.supercasa import SupercasaScraper
from scrapers.casasapo import CasaSapoScraper
from scrapers.remax import RemaxScraper
from scrapers.olx import OLXScraper
from scrapers.utils import slugify_pt

DISTRICTS = [
    "Aveiro", "Beja", "Braga", "Bragança", "Castelo Branco", "Coimbra", "Évora",
    "Faro", "Guarda", "Leiria", "Lisboa", "Portalegre", "Porto", "Santarém",
    "Setúbal", "Viana do Castelo", "Vila Real", "Viseu"
]

SCRAPERS = {
    "idealista": IdealistaScraper(),
    "imovirtual": ImovirtualScraper(),
    "supercasa": SupercasaScraper(),
    "casasapo": CasaSapoScraper(),
    "remax": RemaxScraper(),
    "olx": OLXScraper(),
}

CACHE = TTLCache(maxsize=256, ttl=600)  # 10 min

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
            txt = (x.get("title","") + " " + x.get("snippet","")).lower()
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
        txt = (x.get("title", "") + " " + x.get("snippet", "")).strip()
        if rx.search(txt):
            out.append(x)
    return out


def get_listings(district, pages, sources, filters, sort, limit, typology):
    if district not in DISTRICTS:
        district = "Leiria"

    district_slug = slugify_pt(district)
    sources = [s for s in sources if s in SCRAPERS]

    cache_key = (district, district_slug, pages, tuple(sorted(sources)), _normalize_typology(typology))
    if cache_key in CACHE:
        items = CACHE[cache_key]
    else:
        items = []
        # concorrência por fonte (cada scraper faz as páginas por ordem com pausas leves)
        with ThreadPoolExecutor(max_workers=min(8, len(sources) or 1)) as ex:
            futs = []
            for s in sources:
                futs.append(ex.submit(SCRAPERS[s].scrape, district, district_slug, pages, typology))
            for f in as_completed(futs):
                try:
                    items.extend(f.result())
                except Exception:
                    # não aborta tudo se uma fonte falhar
                    pass

        # dedupe por URL
        seen = set()
        deduped = []
        for x in items:
            u = x.get("url")
            if not u or u in seen:
                continue
            seen.add(u)
            deduped.append(x)
        items = deduped

        CACHE[cache_key] = items

    # Filtro adicional por tipologia (por segurança), sobretudo útil quando uma fonte não suporta o filtro via URL
    items = _apply_typology(items, typology)

    items = _apply_filters(items, filters)
    items = _sort(items, sort)
    items = items[:limit]
    return items, _stats(items)
