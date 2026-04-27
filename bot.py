import feedparser
import requests
import json
import os
import hashlib

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
SENT_FILE = "sent_hashes.json"

FEEDS = [
    "https://feeds.reuters.com/reuters/worldNews",
    "http://www.aljazeera.com/xml/rss/all.xml",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.theguardian.com/world/rss",
    "https://www.politico.com/rss/politics08.xml",
]

KEYWORDS = [
    "iran", "tehran", "khamenei", "irgc", "nuclear", "hormuz",
    "israel", "netanyahu", "idf", "gaza", "hezbollah", "hamas",
    "lebanon", "houthi", "yemen", "red sea",
    "ukraine", "russia", "putin", "zelensky", "nato",
    "trump", "election", "fed rate", "federal reserve",
    "taiwan", "china", "xi jinping",
    "bitcoin", "crypto", "recession", "inflation",
    "ceasefire", "airstrike", "missile", "sanction", "coup", "assassination",
]

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

def summarize(title, summary):
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "max_tokens": 120,
                "messages": [
                    {
                        "role": "system",
                        "content": "Du bist ein Nachrichtenassistent. Fasse die News in 2-3 kurzen deutschen Sätzen zusammen. Fokus auf: was passiert, wer ist beteiligt, Auswirkungen auf Märkte/Polymarket."
                    },
                    {
                        "role": "user",
                        "content": f"Titel: {title}\n\nInhalt: {summary}"
                    }
                ]
            },
            timeout=15
        )
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Groq error: {e}")
        return summary[:200] if summary else ""

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

def main():
    sent = load_sent()
    new_articles = []

    for feed_url in FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:15]:
                title = entry.get("title", "")
                link = entry.get("link", "")
                summary = entry.get("summary", "")
                h = item_hash(title, link)

                if h in sent:
                    continue
                if not is_relevant(title, summary):
                    continue

                new_articles.append((title, link, summary, h))
        except Exception as e:
            print(f"Feed error {feed_url}: {e}")

    for title, link, summary, h in new_articles[:8]:
        ai_summary = summarize(title, summary)
        msg = f"📰 <b>{title}</b>\n\n{ai_summary}\n\n🔗 {link}"
        send_telegram(msg)
        sent.add(h)

    save_sent(sent)
    print(f"Sent {len(new_articles[:8])} articles.")

if __name__ == "__main__":
    main()
