from scrapers.base import BaseScraper
from scrapers.utils import parse_eur_amount, parse_area_m2, parse_eur_m2, absolutize


class OLXScraper(BaseScraper):
    name = "olx"
    base = "https://www.olx.pt"

    def build_url(self, district_slug: str, page: int, typology: str = "T2", search_type: str = "rent") -> str:
        # OLX (PT) estrutura típica com /d/<distrito>/imoveis/apartamentos-casas-para-alugar/
        # ou /d/<distrito>/imoveis/apartamentos-casas-para-vender/
        # Pesquisa por tipologia via query ?q=tN (texto livre), paginação ?page=N
        mode = "alugar" if search_type == "rent" else "vender"
        url = f"{self.base}/d/{district_slug}/imoveis/apartamentos-casas-para-{mode}/"
        params = []
        t = (typology or "T2").upper().replace(" ", "")
        if t not in {"T*", "*"}:
            params.append(f"q={t.lower()}")
        if page > 1:
            params.append(f"page={page}")
        if params:
            url += "?" + "&".join(params)
        return url

    def parse_listings(self, html: str, district_name: str):
        soup = self.soup(html)
        items = []

        # Âncoras de anúncio: preferir seletores estáveis usados pelo OLX
        anchors = []
        anchors.extend(soup.select('a[data-cy="listing-ad-title"]'))
        anchors.extend(soup.select('a[data-testid="ad-title"]'))
        anchors.extend(soup.select('a[href^="/d/anuncio/"]'))

        seen_hrefs = set()
        for a in anchors:
            href = a.get("href")
            if not href or href in seen_hrefs:
                continue
            seen_hrefs.add(href)

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

    def scrape(self, district_name: str, district_slug: str, pages: int, typology: str = "T2", search_type: str = "rent"):
        out = []
        for page in range(1, pages + 1):
            url = self.build_url(district_slug, page, typology, search_type)
            html = self.fetch(url)
            out.extend(self.parse_listings(html, district_name))
            self.polite_sleep()
        return out
