from scrapers.base import BaseScraper
from scrapers.utils import parse_eur_amount, parse_area_m2, parse_eur_m2, absolutize

class RemaxScraper(BaseScraper):
    name = "remax"
    base = "https://remax.pt"

    def build_url(self, district_slug: str, page: int) -> str:
        # /pt/arrendar/apartamento/t2/<distrito>
        # paginação varia (às vezes é scroll), então mantemos por agora page=1..N com tentativa simples
        url = f"{self.base}/pt/arrendar/apartamento/t2/{district_slug}"
        if page > 1:
            url += f"?page={page}"
        return url

    def parse_listings(self, html: str, district_name: str):
        soup = self.soup(html)
        items = []

        # links de detalhe geralmente /pt/imoveis/arrendamento-...
        for a in soup.select('a[href^="/pt/imoveis/arrendamento-"]'):
            href = a.get("href")
            if not href:
                continue

            card = a
            for _ in range(7):
                if card is None:
                    break
                txt = card.get_text(" ", strip=True)
                if "€" in txt and "m²" in txt:
                    break
                card = card.parent

            txt = (card.get_text(" ", strip=True) if card else a.get_text(" ", strip=True))

            price = parse_eur_amount(txt)
            area = parse_area_m2(txt)
            eur_m2 = parse_eur_m2(txt)
            if eur_m2 is None and price is not None and area:
                eur_m2 = round(price / area, 2)

            if price is None and area is None:
                continue

            items.append({
                "source": self.name,
                "district": district_name,
                "title": a.get_text(" ", strip=True) or "RE/MAX",
                "price_eur": price,
                "area_m2": area,
                "eur_m2": eur_m2,
                "url": absolutize(self.base, href),
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
