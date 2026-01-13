from scrapers.base import BaseScraper
from scrapers.utils import parse_eur_amount, parse_area_m2, parse_eur_m2, absolutize


class OLXScraper(BaseScraper):
    name = "olx"
    base = "https://www.olx.pt"

    def build_url(self, district_slug: str, page: int) -> str:
        # OLX (PT) estrutura típica com /d/<distrito>/ ... e pesquisa por T2
        # Exemplo esperado: /d/lisboa/imoveis/apartamentos-casas-arrendamento/apartamentos/q-t2/?page=2
        url = (
            f"{self.base}/d/{district_slug}/imoveis/"
            f"apartamentos-casas-arrendamento/apartamentos/q-t2/"
        )
        if page > 1:
            url += f"?page={page}"
        return url

    def parse_listings(self, html: str, district_name: str):
        soup = self.soup(html)
        items = []

        # Âncoras de anúncio: costumam começar com /d/anuncio/
        for a in soup.select('a[href^="/d/anuncio/"]'):
            href = a.get("href")
            if not href:
                continue

            # Encontra o cartão pai para recolher preço/área em texto
            card = a
            for _ in range(7):
                if card is None:
                    break
                txt = card.get_text(" ", strip=True)
                if "€" in txt or "m²" in txt or "Área" in txt:
                    break
                card = card.parent

            txt = (card.get_text(" ", strip=True) if card else a.get_text(" ", strip=True))
            price = parse_eur_amount(txt)
            area = parse_area_m2(txt)
            eur_m2 = parse_eur_m2(txt)

            if eur_m2 is None and price is not None and area:
                eur_m2 = round(price / area, 2)

            # Filtra anúncios sem qualquer dado útil
            if price is None and area is None:
                continue

            items.append({
                "source": self.name,
                "district": district_name,
                "title": a.get_text(" ", strip=True) or "OLX",
                "price_eur": price,
                "area_m2": area,
                "eur_m2": eur_m2,
                "url": absolutize(self.base, href),
                "snippet": txt[:240],
            })

        # Dedupe interno por URL
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
