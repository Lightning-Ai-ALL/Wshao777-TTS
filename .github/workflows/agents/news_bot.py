import feedparser
import hashlib
import re
from datetime import datetime
from typing import List, Dict

class NewsBot:
    def __init__(self, rss_url: str = "https://news.google.com/rss/search?q=風力發電+AI&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"):
        self.rss_url = rss_url

    def fetch_latest(self, limit: int = 3) -> List[Dict]:
        feed = feedparser.parse(self.rss_url)
        news_list = []
        for entry in feed.entries[:limit]:
            summary = entry.summary if 'summary' in entry else entry.description
            clean_summary = re.sub(r'<[^>]+>', '', summary)[:200]
            news_list.append({
                "headline": entry.title,
                "source": entry.link,
                "summary": clean_summary,
                "published": entry.get('published', datetime.now().isoformat()),
                "news_id": hashlib.md5(entry.title.encode()).hexdigest()[:8]
            })
        return news_list

if __name__ == "__main__":
    bot = NewsBot()
    news = bot.fetch_latest()
    print(news)
