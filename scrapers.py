import requests
from bs4 import BeautifulSoup
import re

class PcComponentesScraper:
    def __init__(self, cfg):
        self.url = "https://www.pccomponentes.com/ofertas-especiales"

    def scrape(self):
        items = []
        r = requests.get(self.url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")

        for product in soup.select(".c-product-card"):
            title_el = product.select_one(".c-product-card__title")
            price_el = product.select_one(".c-product-card__prices-actual")
            link_el = product.select_one("a.c-product-card__title-link")

            if not title_el or not price_el or not link_el:
                continue

            title = title_el.get_text(strip=True)
            price_text = price_el.get_text(strip=True)
            price_match = re.search(r"([\d,.]+)", price_text)
            price = float(price_match.group(1).replace(",", ".")) if price_match else None
            url = "https://www.pccomponentes.com" + link_el["href"]

            items.append({
                "id": re.sub(r"\W+", "_", title.lower())[:50],
                "title": title,
                "price": price,
                "url": url,
                "in_stock": True
            })

        return items


class AmazonDealsScraper:
    def __init__(self, cfg):
        self.url = "https://www.amazon.com/-/es/gp/goldbox?ref_=nav_cs_gb"

    def scrape(self):
        items = []
        r = requests.get(self.url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")

        # Los productos en "Ofertas del Día" suelen estar en este selector
        for deal in soup.select(".DealCard, .a-section.a-text-center.gw-card-layout"):
            title_el = deal.select_one(".DealTitle, .a-text-normal")
            price_el = deal.select_one(".a-price .a-offscreen")
            link_el = deal.select_one("a.a-link-normal")

            if not title_el or not price_el or not link_el:
                continue

            title = title_el.get_text(strip=True)
            price_text = price_el.get_text(strip=True)
            price_match = re.search(r"([\d,.]+)", price_text)
            try:
                price = float(price_match.group(1).replace(",", ".")) if price_match else None
            except:
                price = None
            url = "https://www.amazon.com" + link_el["href"].split("?")[0]

            items.append({
                "id": re.sub(r"\W+", "_", title.lower())[:50],
                "title": title,
                "price": price,
                "url": url,
                "in_stock": True
            })

        return items


def get_site_scraper(site_id, cfg):
    if site_id == "pccomponentes":
        return PcComponentesScraper(cfg)
    elif site_id == "amazon":
        return AmazonDealsScraper(cfg)
    else:
        return None
