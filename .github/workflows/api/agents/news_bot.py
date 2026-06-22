import feedparser
import hashlib
from typing import List, Dict
from datetime import datetime

class NewsBot:
    def __init__(self, rss_url: str = "https://news.google.com/rss/search?q=風力發電+AI&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"):
        self.rss_url = rss_url

    def fetch_latest(self, limit: int = 3) -> List[Dict]:
        """抓取最新新聞並回傳標題、來源與摘要"""
        feed = feedparser.parse(self.rss_url)
        news_list = []
        for entry in feed.entries[:limit]:
            # 產生簡單的內文摘要 (擷取前 200 字)
            summary = entry.summary if 'summary' in entry else entry.description
            # 去除 HTML 標籤
            import re
            clean_summary = re.sub(r'<[^>]+>', '', summary)[:200]
            
            news_list.append({
                "headline": entry.title,
                "source": entry.link,
                "summary": clean_summary,
                "published": entry.get('published', datetime.now().isoformat()),
                "news_id": hashlib.md5(entry.title.encode()).hexdigest()[:8]
            })
        return news_list

# 簡單測試 (可獨立執行)
if __name__ == "__main__":
    bot = NewsBot()
    news = bot.fetch_latest()
    print(news)