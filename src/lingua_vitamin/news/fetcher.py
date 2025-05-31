"""To get news from RSS."""

import logging
from typing import List, Dict

import feedparser

KEY_TITLE = "title"
KEY_CONTENT = "content"


RSS_FEEDS = {
    "de": (
        "https://rss.dw.com/xml/rss-de-top",
        # SPIEGEL ONLINE Main Feed
        "http://www.spiegel.de/schlagzeilen/rss/0,5291,676,00.xml",
        # Academic and Institutional Feeds
        # - Max Delbrück Center (MDC)
        "https://www.mdc-berlin.de/de/rss/articles/news",
        # - Bundesministerium für wirtschaftliche Zusammenarbeit und Entwicklung (BMZ)
        "https://www.bmz.de/de/feed.rss",
        # Zeit Online
        "https://newsfeed.zeit.de/index",
        "https://www.deutschland.de/en/feed-news/rss.xml",
        "https://www.tagesschau.de/infoservices/alle-meldungen-100~rss2.xml",
    ),
    "en": (
        "https://moxie.foxnews.com/google-publisher/latest.xml",
        # Academic and Institutional Feeds
        # - Max Delbrück Center (MDC)
        "https://www.mdc-berlin.de/rss/articles/news",
        # - Bundesministerium für wirtschaftliche Zusammenarbeit und Entwicklung (BMZ)
        "https://www.bmz.de/en/feed.rss",
        "http://news.mit.edu/rss/feed",
        "https://news.harvard.edu/gazette/feed",
        "http://feeds.bbci.co.uk/news/rss.xml",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    ),
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
    urls = RSS_FEEDS.get(lang)
    if isinstance(urls, str):
        urls = (urls,)

    if not urls:
        raise ValueError(f"No RSS feed configured for language '{lang}'")

    news_items = []
    titles = set()
    for index, url in enumerate(urls):
        logging.info(
            "[%02d/%02d][%s => len = %03d/%03d] Processing %s ...",
            index,
            len(urls),
            lang,
            len(news_items),
            top_n,
            url,
        )

        feed = feedparser.parse(url)
        entries = feed.entries[: top_n * 2]

        for entry in entries:
            title = entry.title if "title" in entry else ""

            if title in titles:
                logging.warning("Duplicate title: `%s`.", title)
                continue
            titles.add(title)

            # Use summary/detail if available, fallback to empty string
            content = (
                entry.get("summary")
                or entry.get("description")
                or (entry.get("content")[0].value if entry.get("content") else "")
            )
            news_items.append({KEY_TITLE: title, KEY_CONTENT: content})

            if len(news_items) >= top_n:
                break

        if len(news_items) >= top_n:
            break

    if len(news_items) < top_n:
        logging.warning(
            "Insufficient number of news: len = %d < %d.", len(news_items), top_n
        )

    return news_items
