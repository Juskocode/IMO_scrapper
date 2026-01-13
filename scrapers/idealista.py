import re
from scrapers.base import BaseScraper
from scrapers.utils import parse_eur_amount, parse_area_m2, parse_eur_m2, absolutize

class IdealistaScraper(BaseScraper):
    name = "idealista"
    base = "https://www.idealista.pt"

    def build_url(self, district_slug: str, page: int) -> str:
        # /arrendar-casas/<distrito>-distrito/com-t2/ + /pagina-2
        path = f"/arrendar-casas/{district_slug}-distrito/com-t2/"
        url = self.base + path
        if page > 1:
            url = url.rstrip("/") + f"/pagina-{page}"
        return url

    def parse_listings(self, html: str, district_name: str):
        soup = self.soup(html)
        items = []
        for art in soup.select("article.item"):
            a = art.select_one("a.item-link")
            if not a or not a.get("href"):
                continue

            text = art.get_text(" ", strip=True)
            price = parse_eur_amount(text)
            area = parse_area_m2(text)
            eur_m2 = parse_eur_m2(text)

            # calcula €/m2 se possível
            if eur_m2 is None and price is not None and area:
                eur_m2 = round(price / area, 2)

            url = absolutize(self.base, a["href"])
            title = a.get_text(" ", strip=True)

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

    def scrape(self, district_name: str, district_slug: str, pages: int):
        out = []
        for page in range(1, pages + 1):
            url = self.build_url(district_slug, page)
            html = self.fetch(url)
            out.extend(self.parse_listings(html, district_name))
            self.polite_sleep()
        return out
