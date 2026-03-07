import re
from scrapers.utils import slugify_pt

def normalize_typology(t: str) -> str:
    """Normalize typology input (e.g., 'T2' or 'T2+1')"""
    if not t:
        return "T2"
    t = t.strip().upper().replace(" ", "")
    if t in {"*", "ALL", "T*"}:
        return "T*"
    if not t.startswith("T"):
        t = "T" + t
    return t

def typology_regex(t: str):
    """Build a regex for matching typology in text"""
    t = normalize_typology(t)
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

def match_property_typology(items, typology):
    """Filter items based on typology regex matching in title/snippet"""
    rx = typology_regex(typology)
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
