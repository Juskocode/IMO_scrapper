import time
import random
import requests
import logging
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("scrapers")

class BaseScraper:
    name = "base"
    base = ""

    def __init__(self):
        self.logger = logging.getLogger(f"scrapers.{self.name}")
        self.session = requests.Session()
        # Use a realistic desktop browser UA and common headers to reduce bot-blocking
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/133.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "max-age=0",
            "Sec-Ch-Ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1"
        })

    def fetch(self, url: str) -> str:
        self.logger.info(f"Fetching URL: {url}")
        from urllib.parse import urlparse
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}/"
        last_exc = None
        
        # For Idealista, Supercasa, and Remax, try to visit the origin first to get cookies
        if self.name in ("idealista", "supercasa", "remax") and not self.session.cookies:
             try:
                 self.logger.info(f"Visiting origin {origin} to get cookies...")
                 # Visit a common entry point first
                 # Use very minimal headers for origin visit
                 h = {"User-Agent": self.session.headers.get("User-Agent"), "Accept": "text/html"}
                 self.session.get(origin, timeout=15, headers=h)
                 self.polite_sleep()
             except:
                 pass

        for attempt in range(2):
            try:
                # Use a Referer that looks like a search engine or the site itself
                headers = {"Referer": origin}
                if attempt > 0:
                     headers["Referer"] = "https://www.google.com/"
                     # Update headers to match a Windows Chrome on retry
                     self.session.headers.update({
                         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                         "Sec-Ch-Ua-Platform": '"Windows"'
                     })

                r = self.session.get(url, timeout=25, headers=headers, allow_redirects=True)
                # Retry on common soft-block status codes
                if r.status_code in (429, 403, 503) and attempt == 0:
                    self.logger.warning(f"Soft-block status code {r.status_code} for {url}. Sleeping and retrying...")
                    self.polite_sleep()
                    continue
                r.raise_for_status()
                return r.text
            except Exception as e:
                last_exc = e
                self.logger.error(f"Error fetching {url} (attempt {attempt+1}): {e}")
                if attempt == 0:
                    self.polite_sleep()
                    continue
        # If we reach here, raise the last exception
        self.logger.error(f"Failed to fetch {url} after retries.")
        raise last_exc

    def soup(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    def polite_sleep(self):
        time.sleep(random.uniform(0.6, 1.3))

    def scrape(self, district_name: str, district_slug: str, pages: int, typology: str = "T2", search_type: str = "rent"):
        raise NotImplementedError
