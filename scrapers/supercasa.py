import re
from scrapers.base import BaseScraper
from scrapers.utils import parse_eur_amount, parse_area_m2, parse_eur_m2, parse_typology, absolutize

class SupercasaScraper(BaseScraper):
    name = "supercasa"
    base = "https://supercasa.pt"

    def build_url(self, district_slug: str, page: int, typology: str = "T2", search_type: str = "rent") -> str:
        # /arrendar-casas/<distrito>-distrito/[com-tN]
        # Trying the older URL structure as it might be less protected
        t = (typology or "T2").upper().replace(" ", "")
        seg = ""
        if t.startswith("T") and "+" not in t and len(t) > 1 and t[1:].isdigit():
            seg = f"/com-{t.lower()}"
        
        mode = "arrendar" if search_type == "rent" else "comprar"
        url = f"{self.base}/{mode}-casas/{district_slug}-distrito{seg}/"
        if page > 1:
            url += f"pagina-{page}"
        return url

    def parse_listings(self, html: str, district_name: str, search_type: str = "rent"):
        soup = self.soup(html)
        items = []

        # Try to find listings in search result cards
        # Updated selectors for Supercasa
        cards = soup.select(".property-card, .listing-item, [class*='card'], [class*='property']")
        self.logger.info(f"Found {len(cards)} potential property cards in Supercasa")

        # Fallback to links if no cards found
        # links de detalhe costumam ser /arrendamento-.../i1234567 ou /venda-.../i1234567
        mode_prefix = "/arrendamento-" if search_type == "rent" else "/venda-"
        for a in soup.select(f'a[href^="{mode_prefix}"], a[href*="/i"]'):
            href = a.get("href")
            if not href:
                continue
            if mode_prefix not in href and "/i" not in href:
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
            typology = parse_typology(txt)

            if eur_m2 is None and price is not None and area:
                eur_m2 = round(price / area, 2)

            title = a.get_text(" ", strip=True) or "Anúncio"
            url = absolutize(self.base, href)

            if not typology:
                typology = parse_typology(title)

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
                "typology": typology,
            })

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
            out.extend(self.parse_listings(html, district_name, search_type))
            self.polite_sleep()
        return out
