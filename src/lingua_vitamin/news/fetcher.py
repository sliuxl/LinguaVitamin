"""To get news from RSS."""

import logging
from typing import List, Dict

import feedparser

KEY_TITLE = "title"
KEY_CONTENT = "content"


MAX_SEQ_LENS = {
    # https://github.com/sliuxl/LinguaVitamin/actions/runs/15366626789/job/43240373877
    # Token indices sequence length is longer than the specified maximum sequence length for this model (1163 > 512). Running this sequence through the model will result in indexing errors
    "de": 512,
    "en": 512,
}

RSS_FEEDS = {
    "de": (
        "https://rss.dw.com/xml/rss-de-top",
        # Academic and Institutional Feeds
        # - Max Delbrück Center (MDC)
        "https://www.mdc-berlin.de/de/rss/articles/news",
        # - Bundesministerium für wirtschaftliche Zusammenarbeit und Entwicklung (BMZ)
        "https://www.bmz.de/de/feed.rss",
        # Zeit Online
        "https://newsfeed.zeit.de/index",
        # "https://www.deutschland.de/en/feed-news/rss.xml",
        "https://www.deutschland.de/de/feed-news/rss.xml",
        "https://www.tagesschau.de/infoservices/alle-meldungen-100~rss2.xml",
    ),
    "en": (
        ("https://www.economist.com/latest/rss.xml", 30),
        ("https://www.economist.com/finance-and-economics/rss.xml", 10),
        ("https://www.economist.com/china/rss.xml", 10),
        ("https://www.economist.com/united-states/rss.xml", 10),
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


def _get_len(content):
    """Get len for a str."""
    return len(content.strip().split())


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

    max_len_limit = MAX_SEQ_LENS.get(lang, 0)
    max_len = 0

    news_items = []
    titles = set()
    for index, url in enumerate(urls):
        max_count = top_n * 2
        if not isinstance(url, str):
            url, temp_max_count = url
            max_count = min(max_count, temp_max_count)

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
        entries = feed.entries[:max_count]

        for entry in entries:
            title = entry.title if "title" in entry else ""

            if title in titles:
                logging.warning("Duplicate title: `%s`.", title)
                continue

            # Use summary/detail if available, fallback to empty string
            content = (
                entry.get("summary")
                or entry.get("description")
                or (entry.get("content")[0].value if entry.get("content") else "")
            )

            if max_len_limit and (
                _get_len(content) > max_len_limit or _get_len(title) > max_len_limit
            ):
                logging.warning(
                    "News is too long (title: `%s`): len = (%d, %d) > %d.",
                    title,
                    _get_len(title),
                    _get_len(content),
                    max_len_limit,
                )
                continue

            max_len = max(max_len, _get_len(title), _get_len(content))

            titles.add(title)
            news_items.append({KEY_TITLE: title, KEY_CONTENT: content})

            if len(news_items) >= top_n:
                break

        if len(news_items) >= top_n:
            break

    if len(news_items) < top_n:
        logging.warning(
            "Insufficient number of news: len = %d < %d.", len(news_items), top_n
        )
    logging.info("[%s] Max len for %d news = %d.", lang, len(news_items), max_len)

    return news_items
