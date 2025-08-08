# Simple scrapers with heuristics for deals pages.
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re, time, random, logging

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def _get(url, **kwargs):
    # small randomized delay to reduce risk of blocks
    time.sleep(random.uniform(0.5, 1.2))
    return requests.get(url, headers=HEADERS, timeout=15, **kwargs)

class BaseScraper:
    def __init__(self, cfg):
        self.cfg = cfg
    def scrape(self):
        return []

class AmazonESScraper(BaseScraper):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.base = "https://www.amazon.es"
        # deals page (general)
        self.deals_url = "https://www.amazon.es/gp/goldbox"
    def scrape(self):
        r = _get(self.deals_url)
        soup = BeautifulSoup(r.text, "html.parser")
        products = []
        # heuristic: find links with /dp/ASIN or /gp/product/
        for a in soup.find_all("a", href=True):
            href = a["href"]
            m = re.search(r"/(dp|gp/product)/([A-Z0-9]{10})", href)
            if m:
                asin = m.group(2)
                url = urljoin(self.base, href.split("?")[0])
                item = self._scrape_product_page(url, asin)
                if item:
                    products.append(item)
                    if len(products) >= 30:
                        break
        return products

    def _scrape_product_page(self, url, asin):
        try:
            r = _get(url)
            soup = BeautifulSoup(r.text, "html.parser")
            title_tag = soup.find(id="productTitle")
            title = title_tag.get_text(strip=True) if title_tag else soup.title.string if soup.title else "Producto Amazon"
            # price from common ids
            price = None
            for pid in ("priceblock_ourprice", "priceblock_dealprice", "priceblock_saleprice"):
                tag = soup.find(id=pid)
                if tag:
                    txt = tag.get_text()
                    price = self._parse_price(txt)
                    break
            # fallback: look for meta property
            if price is None:
                m = re.search(r'(\d+[.,]\d{2})\s*€', r.text)
                if m:
                    price = float(m.group(1).replace(",","."))
            in_stock = True
            if soup.find(text=re.compile("Actualmente no disponible|Sin stock|Agotado")):
                in_stock = False
            return {"id": asin, "title": title, "price": price, "in_stock": in_stock, "url": url}
        except Exception as e:
            logging.debug("Amazon product parse error %s: %s", url, e)
            return None

    def _parse_price(self, txt):
        m = re.search(r'(\d+[.,]\d{2})', txt)
        if not m:
            return None
        return float(m.group(1).replace(",","."))

class PcComponentesScraper(BaseScraper):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.base = "https://www.pccomponentes.com"
        self.deals_url = "https://www.pccomponentes.com/ofertas"
    def scrape(self):
        r = _get(self.deals_url)
        soup = BeautifulSoup(r.text, "html.parser")
        products = []
        for card in soup.select("div.producto, div.box-producto")[:60]:
            a = card.find("a", href=True)
            if not a:
                continue
            url = urljoin(self.base, a["href"].split("?")[0])
            title = a.get("title") or a.get_text(strip=True)[:200]
            # price
            price = None
            ptag = card.select_one(".precio, .precio-main, .product-price")
            if ptag:
                txt = ptag.get_text()
                m = re.search(r'(\d+[.,]\d{2})\s*€', txt)
                if m:
                    price = float(m.group(1).replace(",","."))
            # id: use url path
            pid = a["href"].strip("/").split("/")[-1]
            in_stock = True
            if card.select_one(".agotado") or "sin stock" in card.get_text().lower():
                in_stock = False
            products.append({"id": pid, "title": title, "price": price, "in_stock": in_stock, "url": url})
        return products

class FnacScraper(BaseScraper):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.base = "https://www.fnac.es"
        self.deals_url = "https://www.fnac.es/Ofertas"
    def scrape(self):
        try:
            r = _get(self.deals_url)
            soup = BeautifulSoup(r.text, "html.parser")
            products = []
            for item in soup.select(".Article-item")[:50]:
                a = item.find("a", href=True)
                if not a: continue
                url = urljoin(self.base, a["href"].split("?")[0])
                title = a.get("title") or a.get_text(strip=True)[:200]
                price = None
                m = re.search(r'(\d+[.,]\d{2})\s*€', item.get_text())
                if m:
                    price = float(m.group(1).replace(",","."))
                pid = url
                in_stock = "agotado" not in item.get_text().lower()
                products.append({"id": pid, "title": title, "price": price, "in_stock": in_stock, "url": url})
            return products
        except Exception as e:
            return []

class MediaMarktScraper(BaseScraper):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.base = "https://www.mediamarkt.es"
        self.deals_url = "https://www.mediamarkt.es/ofertas"
    def scrape(self):
        try:
            r = _get(self.deals_url)
            soup = BeautifulSoup(r.text, "html.parser")
            products = []
            for card in soup.select(".product-pod, .product")[:60]:
                a = card.find("a", href=True)
                if not a: continue
                url = urljoin(self.base, a["href"].split("?")[0])
                title = a.get("title") or a.get_text(strip=True)[:200]
                price = None
                m = re.search(r'(\d+[.,]\d{2})\s*€', card.get_text())
                if m:
                    price = float(m.group(1).replace(",","."))
                pid = url
                in_stock = "agotado" not in card.get_text().lower()
                products.append({"id": pid, "title": title, "price": price, "in_stock": in_stock, "url": url})
            return products
        except Exception:
            return []

def get_site_scraper(site_id, cfg):
    mapping = {
        "amazon_es": AmazonESScraper,
        "pccomponentes": PcComponentesScraper,
        "fnac": FnacScraper,
        "mediamarkt": MediaMarktScraper
    }
    cls = mapping.get(site_id)
    if cls:
        return cls(cfg)
    return None
