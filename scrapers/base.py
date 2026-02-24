import time
import random
import requests
from bs4 import BeautifulSoup

class BaseScraper:
    name = "base"
    base = ""

    def __init__(self):
        self.session = requests.Session()
        # Use a realistic desktop browser UA and common headers to reduce bot-blocking
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.7",
        })

    def fetch(self, url: str) -> str:
        # Add a simple retry and a reasonable timeout; set Referer to the site origin
        from urllib.parse import urlparse
        parsed = urlparse(url)
        referer = f"{parsed.scheme}://{parsed.netloc}/"
        last_exc = None
        for attempt in range(2):
            try:
                r = self.session.get(url, timeout=25, headers={"Referer": referer}, allow_redirects=True)
                # Retry on common soft-block status codes
                if r.status_code in (429, 403, 503) and attempt == 0:
                    self.polite_sleep()
                    continue
                r.raise_for_status()
                return r.text
            except Exception as e:
                last_exc = e
                if attempt == 0:
                    self.polite_sleep()
                    continue
        # If we reach here, raise the last exception
        raise last_exc

    def soup(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    def polite_sleep(self):
        time.sleep(random.uniform(0.6, 1.3))

    def scrape(self, district_name: str, district_slug: str, pages: int, typology: str = "T2", search_type: str = "rent"):
        raise NotImplementedError
