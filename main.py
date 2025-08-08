#!/usr/bin/env python3
import os, sys, yaml, json, time, logging
from datetime import datetime
from scrapers import get_site_scraper
from storage import StateStore
from twitter_poster import TwitterPoster

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

ROOT = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(ROOT, "config.yaml")
STATE_PATH = os.path.join(ROOT, "data", "state.json")
os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    cfg = load_config()
    twitter = TwitterPoster.from_env()
    store = StateStore(STATE_PATH)
    sites = cfg.get("sites", [])
    template = cfg.get("tweet_template", "{title} — {price}€ {url}")
    any_enabled = any(s.get("enabled", False) for s in sites)
    if not any_enabled:
        logging.warning("No sites enabled in config.yaml — exiting.")
        return 0
    alerts = []
    for site_cfg in sites:
        if not site_cfg.get("enabled", False):
            continue
        scraper = get_site_scraper(site_cfg["id"], site_cfg)
        if not scraper:
            logging.warning("No scraper for %s", site_cfg["id"])
            continue
        logging.info("Scraping %s", site_cfg["name"])
        try:
            items = scraper.scrape()
        except Exception as e:
            logging.exception("Error scraping %s: %s", site_cfg["id"], e)
            continue
        for item in items:
            key = f\"{site_cfg['id']}|{item['id']}\"
            previous = store.get(key)
            should_alert = False
            reason = None
            # Price-based alert
            threshold = site_cfg.get("price_threshold_eur")
            if item.get("price") is not None and threshold is not None:
                if item["price"] <= threshold and (not previous or previous.get("price", 999999) > item["price"]):
                    should_alert = True
                    reason = f\"price_below_threshold ({item['price']} <= {threshold})\"
            # Stock-reavailability alert
            if item.get("in_stock") and previous and not previous.get("in_stock", False):
                should_alert = True
                reason = "back_in_stock"
            if should_alert:
                text = template.format(title=item.get("title","(sin título)")[:200], price=f\"{item.get('price')}\", url=item.get("url"))
                alerts.append((key, item, text, reason))
            # update store regardless
            store.set(key, {"price": item.get("price"), "in_stock": item.get("in_stock"), "last_seen": datetime.utcnow().isoformat()})
    # Post alerts
    for key, item, text, reason in alerts:
        logging.info("Alerting %s — %s", key, reason)
        try:
            twitter.post(text)
        except Exception as e:
            logging.exception("Failed to post tweet: %s", e)
    store.save()
    logging.info("Run complete. Alerts posted: %d", len(alerts))
    return 0

if __name__ == "__main__":
    sys.exit(main())
