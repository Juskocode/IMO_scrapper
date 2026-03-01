import re
from scrapers.base import BaseScraper
from scrapers.utils import parse_eur_amount, parse_area_m2, parse_eur_m2, parse_typology, absolutize

class CasaSapoScraper(BaseScraper):
    name = "casasapo"
    base = "https://casa.sapo.pt"

    def build_url(self, district_slug: str, page: int, typology: str = "T2", search_type: str = "rent") -> str:
        # /alugar-apartamentos/tN/distrito.<distrito>/?pn=2
        # /comprar-apartamentos/tN/distrito.<distrito>/?pn=2
        t = (typology or "T2").upper().replace(" ", "")
        typseg = "t2"
        if t.startswith("T") and "+" not in t and len(t) > 1 and t[1:].isdigit():
            typseg = t.lower()
        
        mode = "alugar" if search_type == "rent" else "comprar"
        url = f"{self.base}/{mode}-apartamentos/{typseg}/distrito.{district_slug}/"
        if page > 1:
            url += f"?pn={page}"
        return url

    def parse_listings(self, html: str, district_name: str, search_type: str = "rent"):
        soup = self.soup(html)
        items = []
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            txt = a.get_text(" ", strip=True)
            # cartões no texto costumam ter "m²" e "alugar <preço> €" ou "comprar <preço> €"
            if "m²" not in txt or "€" not in txt:
                continue
            if "Apartamento" not in txt and "T2" not in txt:
                continue
            
            mode_kw = "alugar" if search_type == "rent" else "venda" # casa.sapo uses 'alugar' or 'venda' in text?
            # Actually, let's be more flexible with keywords in text
            if search_type == "rent":
                 if "alugar" not in txt.lower() and "arrendar" not in txt.lower():
                     continue
            else:
                 # for buy, it might be "venda" or just price
                 pass

            url = absolutize(self.base, href)
            price = parse_eur_amount(txt)
            area = parse_area_m2(txt)
            eur_m2 = parse_eur_m2(txt)
            typology = parse_typology(txt)

            if eur_m2 is None and price is not None and area:
                eur_m2 = round(price / area, 2)

            items.append({
                "source": self.name,
                "district": district_name,
                "title": txt[:90],
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
