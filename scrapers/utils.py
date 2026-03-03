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

def parse_typology(text: str):
    if not text:
        return None
    # Try to find T0, T1, T2, T2+1, etc.
    # Matches: T2, T 2, T2+1, T 2 + 1, etc.
    m = re.search(r"\bT\s*(\d+(?:\s*\+\s*\d+)?)\b", text, re.IGNORECASE)
    if m:
        t_val = m.group(1).replace(" ", "").upper()
        return "T" + t_val
    return None

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

def parse_portuguese_date(text: str):
    if not text:
        return None
    
    import datetime
    
    # "Publicado 26 de fevereiro de 2026"
    # "Ontem às 15:30"
    # "Hoje às 10:20"
    # "15 de jan."
    
    months = {
        "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4, "maio": 5, "junho": 6,
        "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
        "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
        "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12
    }
    
    t = text.lower().strip()
    now = datetime.datetime.now()
    
    # Formato: "Publicado 26 de fevereiro de 2026"
    m = re.search(r"(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(\d{4})", t)
    if m:
        day = int(m.group(1))
        month_name = m.group(2)
        year = int(m.group(3))
        month = months.get(month_name, 1)
        return datetime.datetime(year, month, day).isoformat()
    
    # Formato: "26 de fevereiro" (assume ano corrente)
    m = re.search(r"(\d{1,2})\s+de\s+([a-zç]+)", t)
    if m:
        day = int(m.group(1))
        month_name = m.group(2)
        month = months.get(month_name)
        if month:
            # Se o mês já passou, assume este ano. Se for um mês futuro, pode ser do ano passado.
            year = now.year
            if month > now.month:
                year -= 1
            return datetime.datetime(year, month, day).isoformat()

    # Formato: "Hoje às 15:30"
    if "hoje" in t:
        m = re.search(r"(\d{1,2}):(\d{2})", t)
        if m:
            h, mi = int(m.group(1)), int(m.group(2))
            return now.replace(hour=h, minute=mi, second=0, microsecond=0).isoformat()
        return now.isoformat()

    # Formato: "Ontem às 15:30"
    if "ontem" in t:
        yesterday = now - datetime.timedelta(days=1)
        m = re.search(r"(\d{1,2}):(\d{2})", t)
        if m:
            h, mi = int(m.group(1)), int(m.group(2))
            return yesterday.replace(hour=h, minute=mi, second=0, microsecond=0).isoformat()
        return yesterday.isoformat()

    # Formato: "há 2 dias", "2 dias atrás"
    m = re.search(r"(?:há|ha)\s+(\d+)\s+dias", t)
    if m:
        days = int(m.group(1))
        return (now - datetime.timedelta(days=days)).isoformat()
    
    # Formato: "há 2 horas"
    m = re.search(r"(?:há|ha)\s+(\d+)\s+horas", t)
    if m:
        hours = int(m.group(1))
        return (now - datetime.timedelta(hours=hours)).isoformat()
        
    # Formato: "agora mesmo", "há instantes"
    if "agora mesmo" in t or "instantes" in t:
        return now.isoformat()

    return None

def absolutize(base: str, href: str) -> str:
    return urljoin(base, href)
