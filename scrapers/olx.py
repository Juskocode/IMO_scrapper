from scrapers.base import BaseScraper
from scrapers.utils import parse_eur_amount, parse_area_m2, parse_eur_m2, absolutize


class OLXScraper(BaseScraper):
    name = "olx"
    base = "https://www.olx.pt"

    def build_url(self, district_slug: str, page: int, typology: str = "T2", search_type: str = "rent") -> str:
        # OLX (PT) - Using the search endpoint
        # mode = "alugar" if search_type == "rent" else "venda"
        # The base URL should be https://www.olx.pt/imoveis/
        url = f"{self.base}/imoveis/"
        
        mode_pt = "alugar" if search_type == "rent" else "venda"
        t = (typology or "T2").upper().replace(" ", "")
        url += f"?q={district_slug}+{t.lower()}+{mode_pt}"
        
        if page > 1:
            url += f"&page={page}"
            
        return url

    def parse_listings(self, html: str, district_name: str):
        import json
        import re
        items = []

        # OLX uses a JSON blob in window.__PRERENDERED_STATE__
        # and also has structured data in ld+json
        
        # 1. Try ld+json first as it's very clean for titles, prices, and URLs
        ld_json_matches = re.findall(r'<script [^>]*type="application/ld\+json">({.*?})</script>', html)
        ld_ads = {}
        for match_str in ld_json_matches:
            try:
                data = json.loads(match_str)
                if data.get("@type") == "Product" and "offers" in data:
                    offers = data["offers"].get("offers", [])
                    for off in offers:
                        url = off.get("url")
                        if url:
                            ld_ads[url] = {
                                "price": off.get("price"),
                                "title": off.get("name")
                            }
            except:
                continue

        # 2. Try window.__PRERENDERED_STATE__ for areas (m2)
        match = re.search(r'window\.__PRERENDERED_STATE__\s*=\s*"({.*?})"', html)
        if match:
            try:
                # The JSON is escaped inside the string
                json_str = match.group(1).replace('\\"', '"').replace('\\\\', '\\')
                data = json.loads(json_str)
                
                # Path: listing -> listing -> ads
                ads = data.get("listing", {}).get("listing", {}).get("ads", [])
                self.logger.info(f"Found {len(ads)} ads in OLX JSON data")
                
                for ad in ads:
                    if not isinstance(ad, dict):
                        continue
                    title = ad.get("title")
                    url = ad.get("url")
                    if not title or not url:
                        continue
                    
                    # Get price from ld_ads if possible (more reliable), else from here
                    price = None
                    if url in ld_ads:
                        price = ld_ads[url].get("price")
                    
                    if price is None:
                        price_info = ad.get("price", {})
                        if isinstance(price_info, dict):
                            # In some versions it might be here
                            price = price_info.get("value")
                            if isinstance(price, dict):
                                price = price.get("value")
                        else:
                            price = price_info
                    
                    # Area and other params are in 'params' list
                    area = None
                    params = ad.get("params", [])
                    for p in params:
                        if p.get("key") in ("area", "m2", "area_util"):
                            val = p.get("normalizedValue")
                            if val:
                                try:
                                    area = float(val)
                                except:
                                    pass
                            break
                    
                    eur_m2 = None
                    if price and area:
                        try:
                            eur_m2 = round(float(price) / area, 2)
                        except:
                            pass
                    
                    items.append({
                        "source": self.name,
                        "district": district_name,
                        "title": title,
                        "price_eur": float(price) if price else None,
                        "area_m2": area,
                        "eur_m2": eur_m2,
                        "url": url,
                        "snippet": title,
                    })
                
                if items:
                    return items
            except Exception as e:
                self.logger.error(f"Error parsing OLX JSON: {e}")

        # Fallback to HTML parsing if JSON fails (not implemented here as JSON is main)
        return items

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
