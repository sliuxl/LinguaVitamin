"""To get papers from arXiv."""

import datetime
import logging
from typing import List, Dict

import feedparser

KEY_ABSTRACT_RAW = "summary"
KEY_ABSTRACT = "abstract"
KEY_AUTHORS = "authors"
KEY_DATE_RAW = "updated"
KEY_DATE = "date"
KEY_TITLE = "title"
KEY_URL_RAW = "id"
KEY_URL = "url"


# http://export.arxiv.org/api/query?search_query=cat:cs.DC+AND+lastUpdatedDate:[20240529+TO+20240531]&sortBy=lastUpdatedDate&sortOrder=descending
RSS_FEED = "http://export.arxiv.org/api/query?search_query=cat:{arxiv_subject}+AND+lastUpdatedDate:[{date_start}+TO+{date_end}]&sortBy=lastUpdatedDate&sortOrder=descending&max_results={top_n}"

RSS_FEED_MAP = {
    "hacker-news": "https://hnrss.org/best",
}


def _normalize(text: str) -> str:
    return " ".join(text.split("\n"))


def _fetch(
    subject: str,
    top_n: int = 1000,
) -> List[Dict[str, str]]:
    """Fetch hacker news from its API.

    <item>
    <title>
    <![CDATA[ After court order, OpenAI is now preserving all ChatGPT user logs ]]>
    </title>
    <description>
    <![CDATA[ <p>Article URL: <a href="https://mastodon.laurenweinstein.org/@lauren/114627064774788581">https://mastodon.laurenweinstein.org/@lauren/114627064774788581</a></p> <p>Comments URL: <a href="https://news.ycombinator.com/item?id=44185913">https://news.ycombinator.com/item?id=44185913</a></p> <p>Points: 513</p> <p># Comments: 355</p> ]]>
    </description>
    <pubDate>Wed, 04 Jun 2025 21:47:33 +0000</pubDate>
    <link>https://mastodon.laurenweinstein.org/@lauren/114627064774788581</link>
    <dc:creator>ColinWright</dc:creator>
    <comments>https://news.ycombinator.com/item?id=44185913</comments>
    <guid isPermaLink="false">https://news.ycombinator.com/item?id=44185913</guid>
    </item>
    <item>
    """
    url = RSS_FEED_MAP[subject]
    logging.info("URL: `%s`", url)

    hacker_news = []
    feed = feedparser.parse(url)
    for entry in feed.entries:
        logging.info(entry)
        title = _normalize(entry.get(KEY_TITLE))
        abstract = _normalize(entry.get("summary"))
        date = entry.get("published")
        url = entry.get("link")
        authors = entry.get("author")

        hacker_news.append(
            {
                KEY_TITLE: title,
                KEY_ABSTRACT: abstract,
                KEY_DATE: datetime.datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %z").isoformat(),
                KEY_URL: url,
                KEY_AUTHORS: authors,
            }
        )

        if top_n and len(hacker_news) >= top_n:
            logging.warning(
                "There are too many hacker_news, cut off at %d < %d.", top_n, len(feed)
            )
            break

    logging.info("[%s] Len for %s: %d/ %d.", subject, date, len(hacker_news), top_n)

    return hacker_news


def fetch_arxiv_papers(
    subject: str,
    date: str,
    top_n: int = 1000,
    date_end: str = None,
) -> List[Dict[str, str]]:
    """Fetch arxiv papers from its API."""
    if date_end is None:
        top = 4
        date_end = f"{int(date[:top]) + 1:4d}{date[top:]}"

    if subject in RSS_FEED_MAP:
        return _fetch(subject, top_n=top_n)

    url = RSS_FEED.format(
        arxiv_subject=subject, date_start=date, date_end=date_end, top_n=top_n
    )
    logging.info("URL: `%s`", url)

    papers = []
    feed = feedparser.parse(url)
    for entry in feed.entries:
        title = _normalize(entry.get(KEY_TITLE))
        abstract = _normalize(entry.get(KEY_ABSTRACT_RAW))
        date = entry.get(KEY_DATE_RAW)
        url = entry.get(KEY_URL_RAW)
        authors = ", ".join([author.name for author in entry.get(KEY_AUTHORS)])

        papers.append(
            {
                KEY_TITLE: title,
                KEY_ABSTRACT: abstract,
                KEY_DATE: date,
                KEY_URL: url,
                KEY_AUTHORS: authors,
            }
        )

        if top_n and len(papers) >= top_n:
            logging.warning(
                "There are too many papers, cut off at %d < %d.", top_n, len(feed)
            )
            break

    logging.info("[%s] Len for %s: %d/ %d.", subject, date, len(papers), top_n)

    return papers
