"""To get news from RSS."""

from typing import List, Dict

import feedparser

KEY_TITLE = "title"
KEY_CONTENT = "content"


RSS_FEEDS = {
    "de": "https://rss.dw.com/xml/rss-de-top",
    "en": "http://feeds.bbci.co.uk/news/rss.xml",
    "es": "https://elpais.com/rss/feed.html?feedId=1022",
    "zh": "http://www.chinadaily.com.cn/rss/china_rss.xml",
}


def fetch_top_news_rss(lang: str = "en", top_n: int = 5) -> List[Dict[str, str]]:
    """
    Fetch top n news items from RSS feed of the given language.
    Each item includes title and content/summary.

    :param lang: Language code
    :param n: Number of news items to fetch
    :return: List of dicts with keys 'title' and 'content'
    """
    url = RSS_FEEDS.get(lang)
    if not url:
        raise ValueError(f"No RSS feed configured for language '{lang}'")

    feed = feedparser.parse(url)
    entries = feed.entries[:top_n]

    news_items = []
    for entry in entries:
        title = entry.title if "title" in entry else ""
        # Use summary/detail if available, fallback to empty string
        content = (
            entry.get("summary")
            or entry.get("description")
            or entry.get("content")[0].value
            if entry.get("content")
            else ""
        )
        news_items.append({KEY_TITLE: title, KEY_CONTENT: content})

    return news_items
