import time
import random
import requests
from bs4 import BeautifulSoup

class BaseScraper:
    name = "base"
    base = ""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) renta-dashboard/1.0",
            "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.7",
        })

    def fetch(self, url: str) -> str:
        r = self.session.get(url, timeout=20)
        r.raise_for_status()
        return r.text

    def soup(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    def polite_sleep(self):
        time.sleep(random.uniform(0.6, 1.3))

    def scrape(self, district_name: str, district_slug: str, pages: int):
        raise NotImplementedError
