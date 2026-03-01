import re
from scrapers.base import BaseScraper
from scrapers.utils import parse_eur_amount, parse_area_m2, parse_eur_m2, parse_typology, absolutize

class ImovirtualScraper(BaseScraper):
    name = "imovirtual"
    base = "https://www.imovirtual.com"

    def build_url(self, district_slug: str, page: int, typology: str = "T2", search_type: str = "rent") -> str:
        # /pt/resultados/arrendar/apartamento%2CtN/<distrito>?page=2
        # /pt/resultados/comprar/apartamento%2CtN/<distrito>?page=2
        t = (typology or "T2").upper().replace(" ", "")
        seg = "apartamento"
        if t.startswith("T") and "+" not in t and len(t) > 1 and t[1:].isdigit():
            seg = f"apartamento%2C{t.lower()}"
        
        mode = "arrendar" if search_type == "rent" else "comprar"
        url = f"{self.base}/pt/resultados/{mode}/{seg}/{district_slug}"
        if page > 1:
            url += f"?page={page}"
        return url

    def parse_listings(self, html: str, district_name: str):
        soup = self.soup(html)
        items = []

        # links típicos de anúncio
        links = soup.select('a[href^="/pt/anuncio/"]')
        for a in links:
            href = a.get("href")
            if not href:
                continue
            url = absolutize(self.base, href)

            # tenta ir ao "cartão" (pai) para apanhar preço/área
            card = a
            for _ in range(6):
                if card is None:
                    break
                txt = card.get_text(" ", strip=True)
                if "€/m²" in txt or "m²" in txt or "€" in txt:
                    break
                card = card.parent

            txt = (card.get_text(" ", strip=True) if card else a.get_text(" ", strip=True))
            price = parse_eur_amount(txt)
            eur_m2 = parse_eur_m2(txt)
            area = parse_area_m2(txt)
            typology = parse_typology(txt)

            if area is None and price is not None and eur_m2:
                area = round(price / eur_m2, 2)

            if eur_m2 is None and price is not None and area:
                eur_m2 = round(price / area, 2)

            title = a.get_text(" ", strip=True)
            if not title:
                continue

            if not typology:
                typology = parse_typology(title)

            items.append({
                "source": self.name,
                "district": district_name,
                "title": title,
                "price_eur": price,
                "area_m2": area,
                "eur_m2": eur_m2,
                "url": url,
                "snippet": txt[:240],
                "typology": typology,
            })

        # dedupe interno
        seen = set()
        out = []
        for x in items:
            if x["url"] in seen:
                continue
            seen.add(x["url"])
            out.append(x)
        return out

    def scrape(self, district_name: str, district_slug: str, pages: int, typology: str = "T2", search_type: str = "rent"):
        out = []
        for page in range(1, pages + 1):
            url = self.build_url(district_slug, page, typology, search_type)
            html = self.fetch(url)
            out.extend(self.parse_listings(html, district_name))
            self.polite_sleep()
        return out
