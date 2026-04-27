import feedparser
import requests
import json
import os
import hashlib
from datetime import datetime, timezone

# ── CONFIG ──────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
SENT_FILE = "sent_hashes.json"

# ── RSS FEEDS ────────────────────────────────────────────────────────────
FEEDS = [
    "https://feeds.reuters.com/reuters/worldNews",
    "https://feeds.reuters.com/Reuters/worldNews",
    "http://www.aljazeera.com/xml/rss/all.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.politico.com/rss/politics08.xml",
    "https://feeds.washingtonpost.com/rss/world",
    "https://www.theguardian.com/world/rss",
]

# ── KEYWORDS (Polymarket-relevant) ───────────────────────────────────────
KEYWORDS = [
    # Iran / Middle East
    "iran", "tehran", "khamenei", "irgc", "nuclear", "strait of hormuz",
    "israel", "netanyahu", "idf", "gaza", "west bank", "hezbollah", "hamas",
    "lebanon", "beirut", "houthi", "yemen", "red sea",
    # Russia / Ukraine
    "ukraine", "russia", "putin", "zelensky", "nato", "crimea", "kharkiv",
    # US Politics
    "trump", "biden", "harris", "election", "supreme court", "congress",
    "fed rate", "federal reserve", "powell",
    # China / Taiwan
    "taiwan", "china", "xi jinping", "pla", "south china sea",
    # Markets / Crypto
    "bitcoin", "crypto", "sec", "etf", "recession", "inflation",
    # General conflict
    "ceasefire", "war", "airstrike", "missile", "sanction", "coup",
    "assassination", "nuclear", "treaty",
]

# ── HELPERS ──────────────────────────────────────────────────────────────
def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE) as f:
            return set(json.load(f))
    return set()

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(list(sent), f)

def is_relevant(title, summary=""):
    text = (title + " " + summary).lower()
    return any(kw in text for kw in KEYWORDS)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    })

def item_hash(title, link):
    return hashlib.md5(f"{title}{link}".encode()).hexdigest()

# ── MAIN ─────────────────────────────────────────────────────────────────
def main():
    sent = load_sent()
    new_articles = []

    for feed_url in FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:20]:
                title = entry.get("title", "")
                link = entry.get("link", "")
                summary = entry.get("summary", "")
                h = item_hash(title, link)

                if h in sent:
                    continue
                if not is_relevant(title, summary):
                    continue

                new_articles.append((title, link, h))
        except Exception as e:
            print(f"Feed error {feed_url}: {e}")

    # Send (max 10 per run to avoid spam)
    for title, link, h in new_articles[:10]:
        msg = f"📰 <b>{title}</b>\n🔗 {link}"
        send_telegram(msg)
        sent.add(h)

    save_sent(sent)
    print(f"Sent {len(new_articles[:10])} new articles.")

if __name__ == "__main__":
    main()
