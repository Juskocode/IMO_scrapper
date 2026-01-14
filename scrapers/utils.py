import re
import unicodedata
from urllib.parse import urljoin

def slugify_pt(s: str) -> str:
    # remove acentos, baixa, espaços -> hífen
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = s.lower().strip()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^a-z0-9\-]+", "", s)
    s = re.sub(r"-{2,}", "-", s)
    return s

def parse_eur_amount(text: str):
    if not text:
        return None
    t = text.replace("\xa0", " ").replace("€/mês", "").replace("/mês", "").strip()
    m = re.search(r"(\d[\d\.\s]*)(?:,(\d+))?\s*€", t)
    if not m:
        return None
    whole = re.sub(r"[\s\.]", "", m.group(1))
    dec = m.group(2) or ""
    try:
        return float(f"{whole}.{dec}") if dec else float(whole)
    except ValueError:
        return None

def parse_area_m2(text: str):
    if not text:
        return None
    t = text.replace("\xa0", " ")
    # aceita m² e m2; tenta padrões "Área bruta 105 m²" / "área bruta" / genérico
    m = re.search(r"area\s*(?:bruta|util|útil)\s*[:\-]?\s*(\d+(?:[.,]\d+)?)\s*m(?:\s*²|\s*2)", t, re.IGNORECASE)
    if not m:
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*m(?:\s*²|\s*2)", t, re.IGNORECASE)
    if not m:
        return None
    v = m.group(1).replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return None

def parse_eur_m2(text: str):
    if not text:
        return None
    t = text.replace("\xa0", " ")
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*€\s*/\s*m²", t)
    if not m:
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*€/m²", t)
    if not m:
        return None
    v = m.group(1).replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return None

def absolutize(base: str, href: str) -> str:
    return urljoin(base, href)
