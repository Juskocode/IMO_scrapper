import re
from scrapers.base import BaseScraper
from scrapers.utils import parse_eur_amount, parse_area_m2, parse_eur_m2, absolutize

class SupercasaScraper(BaseScraper):
    name = "supercasa"
    base = "https://supercasa.pt"

    def build_url(self, district_slug: str, page: int) -> str:
        # /arrendar-casas/<distrito>-distrito/com-t2 + /pagina-2
        url = f"{self.base}/arrendar-casas/{district_slug}-distrito/com-t2"
        if page > 1:
            url += f"/pagina-{page}"
        return url

    def parse_listings(self, html: str, district_name: str):
        soup = self.soup(html)
        items = []

        # links de detalhe costumam ser /arrendamento-.../i1234567
        for a in soup.select('a[href^="/arrendamento-"], a[href*="/i"]'):
            href = a.get("href")
            if not href:
                continue
            if "arrendamento" not in href and "/i" not in href:
                continue

            # tenta capturar o bloco do cartão
            card = a
            for _ in range(7):
                if card is None:
                    break
                txt = card.get_text(" ", strip=True)
                if ("Área" in txt or "m²" in txt) and "€" in txt:
                    break
                card = card.parent

            txt = (card.get_text(" ", strip=True) if card else a.get_text(" ", strip=True))
            price = parse_eur_amount(txt)
            area = parse_area_m2(txt)
            eur_m2 = parse_eur_m2(txt)

            if eur_m2 is None and price is not None and area:
                eur_m2 = round(price / area, 2)

            title = a.get_text(" ", strip=True) or "Anúncio"
            url = absolutize(self.base, href)

            # filtra lixo óbvio
            if price is None and area is None:
                continue

            items.append({
                "source": self.name,
                "district": district_name,
                "title": title,
                "price_eur": price,
                "area_m2": area,
                "eur_m2": eur_m2,
                "url": url,
                "snippet": txt[:240],
            })

        seen = set()
        out = []
        for x in items:
            if x["url"] in seen:
                continue
            seen.add(x["url"])
            out.append(x)
        return out

    def scrape(self, district_name: str, district_slug: str, pages: int):
        out = []
        for page in range(1, pages + 1):
            url = self.build_url(district_slug, page)
            html = self.fetch(url)
            out.extend(self.parse_listings(html, district_name))
            self.polite_sleep()
        return out
