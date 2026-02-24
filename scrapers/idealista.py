import re
from scrapers.base import BaseScraper
from scrapers.utils import parse_eur_amount, parse_area_m2, parse_eur_m2, absolutize

class IdealistaScraper(BaseScraper):
    name = "idealista"
    base = "https://www.idealista.pt"

    def build_url(self, district_slug: str, page: int, typology: str = "T2", search_type: str = "rent") -> str:
        # /arrendar-casas/<distrito>-distrito/[com-tN]/ + /pagina-2
        # /comprar-casas/<distrito>-distrito/[com-tN]/ + /pagina-2
        seg = ""
        t = (typology or "T2").upper().replace(" ", "")
        if t.startswith("T") and "+" not in t and len(t) > 1 and t[1:].isdigit():
            seg = f"com-{t.lower()}/"
        
        mode = "arrendar" if search_type == "rent" else "comprar"
        path = f"/{mode}-casas/{district_slug}-distrito/" + seg
        url = self.base + path
        if page > 1:
            url = url.rstrip("/") + f"/pagina-{page}"
        return url

    def parse_listings(self, html: str, district_name: str):
        soup = self.soup(html)
        items = []

        # Primary pattern: article.item > a.item-link
        anchors = [a for a in soup.select("article.item a.item-link") if a.get("href")]
        # Fallback: any anchor that points to a listing detail like /imovel/12345/
        if not anchors:
            anchors = [a for a in soup.select('a[href*="/imovel/"]') if a.get("href")]

        seen_hrefs = set()
        for a in anchors:
            href = a.get("href")
            if not href or href in seen_hrefs:
                continue
            seen_hrefs.add(href)

            # Try to grab the card text (price/area usually nearby)
            card = a
            for _ in range(7):
                if card is None:
                    break
                txt = card.get_text(" ", strip=True)
                if ("€" in txt) or ("m²" in txt) or ("Área" in txt) or ("area" in txt.lower()):
                    break
                card = card.parent

            text = (card.get_text(" ", strip=True) if card else a.get_text(" ", strip=True))
            price = parse_eur_amount(text)
            area = parse_area_m2(text)
            eur_m2 = parse_eur_m2(text)

            if eur_m2 is None and price is not None and area:
                eur_m2 = round(price / area, 2)

            url = absolutize(self.base, href)
            title = a.get_text(" ", strip=True) or "Idealista"

            items.append({
                "source": self.name,
                "district": district_name,
                "title": title,
                "price_eur": price,
                "area_m2": area,
                "eur_m2": eur_m2,
                "url": url,
                "snippet": text[:240],
            })
        return items

    def scrape(self, district_name: str, district_slug: str, pages: int, typology: str = "T2", search_type: str = "rent"):
        out = []
        for page in range(1, pages + 1):
            url = self.build_url(district_slug, page, typology, search_type)
            html = self.fetch(url)
            out.extend(self.parse_listings(html, district_name))
            self.polite_sleep()
        return out
