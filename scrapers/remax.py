from scrapers.base import BaseScraper
from scrapers.utils import parse_eur_amount, parse_area_m2, parse_eur_m2, parse_typology, absolutize

class RemaxScraper(BaseScraper):
    name = "remax"
    base = "https://remax.pt"

    def build_url(self, district_slug: str, page: int, typology: str = "T2", search_type: str = "rent") -> str:
        # Path-based URLs are more likely to be SSR-friendly on RE/MAX.
        # Format: /pt/[arrendar|comprar]/[apartamento|moradia|...]/[district]/[typology]
        mode = "arrendar" if search_type == "rent" else "comprar"
        
        t = (typology or "T2").upper().replace(" ", "")
        typ_seg = ""
        if t.startswith("T") and t[1:].isdigit():
            typ_seg = f"/{t.lower()}"
        
        # We'll use 'apartamento' as default segment for now as it's the most common search
        # district_slug should be just the name, e.g., 'leiria'
        url = f"{self.base}/pt/{mode}/apartamento/{district_slug}{typ_seg}"
        
        if page > 1:
            # Query param for page seems to work with path-based URLs
            url += f"?page={page}"
            
        return url

    def parse_listings(self, html: str, district_name: str):
        soup = self.soup(html)
        items = []

        self.logger.info(f"Parsing Remax listings. HTML length: {len(html)}")

        # The site uses several classes like 'listing-card', 'property-card', etc.
        cards = soup.select('article, .property-card, .listing-card, [class*="PropertyCard"], [class*="ListingCard"]')
        if not cards:
             # Even broader search
             cards = soup.select('div[class*="listing"], div[class*="property"]')
             
        self.logger.info(f"Found {len(cards)} potential listing cards via HTML")
        
        for card in cards:
            a = card.select_one('a[href*="/imoveis/"], a[href*="/pt/"]')
            if not a:
                # find first link that looks like a detail page
                a = card.find("a", href=True)
                if not a or ("/pt/" not in a['href'] and "/imoveis/" not in a['href']):
                    continue
            
            href = a.get("href")
            txt = card.get_text(" ", strip=True)
            
            # Check for common listing features in text
            if "€" not in txt and "m²" not in txt:
                continue
                
            price = parse_eur_amount(txt)
            area = parse_area_m2(txt)
            eur_m2 = parse_eur_m2(txt)
            typology = parse_typology(txt)
            if eur_m2 is None and price is not None and area:
                eur_m2 = round(price / area, 2)

            if price is None and area is None:
                continue

            title = a.get_text(" ", strip=True) or "RE/MAX"
            if not typology:
                typology = parse_typology(title)

            items.append({
                "source": self.name,
                "district": district_name,
                "title": title,
                "price_eur": price,
                "area_m2": area,
                "eur_m2": eur_m2,
                "url": absolutize(self.base, href),
                "snippet": txt[:240],
                "typology": typology,
            })

        # 3. Final desperate fallback: all links with /imoveis/ or /pt/
        if not items:
            anchors = soup.select('a[href*="/imoveis/"], a[href*="/pt/arrendar/"], a[href*="/pt/comprar/"]')
            self.logger.info(f"Found {len(anchors)} potential listing anchors via raw links")
            seen_hrefs = set()
            for a in anchors:
                href = a.get("href")
                if not href or href in seen_hrefs:
                    continue
                seen_hrefs.add(href)
                
                # Try to find price/area in parent
                card = a
                found = False
                for _ in range(7):
                    if card is None: break
                    ctx = card.get_text(" ", strip=True)
                    if "€" in ctx or "m²" in ctx:
                        found = True
                        break
                    card = card.parent
                
                if not found: continue
                
                txt = card.get_text(" ", strip=True)
                price = parse_eur_amount(txt)
                area = parse_area_m2(txt)
                typology = parse_typology(txt)
                title = a.get_text(" ", strip=True) or "RE/MAX"
                if not typology:
                    typology = parse_typology(title)

                if price or area:
                    items.append({
                        "source": self.name,
                        "district": district_name,
                        "title": title,
                        "price_eur": price,
                        "area_m2": area,
                        "eur_m2": (price/area if price and area else None),
                        "url": absolutize(self.base, href),
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
            out.extend(self.parse_listings(html, district_name))
            self.polite_sleep()
        return out
