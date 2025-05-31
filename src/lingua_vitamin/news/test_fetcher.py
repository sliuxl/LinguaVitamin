"""Unit tests for fetcher.py."""

import logging
import unittest
from parameterized import parameterized

from lingua_vitamin.news import fetcher


_FACTOR = 1

LOGGING_FORMAT = "%(asctime)s [%(filename)s:%(lineno)d] %(levelname)s - %(message)s"


class TestFetcher(unittest.TestCase):
    """Unit tests for fetcher.py."""

    @parameterized.expand(
        [
            ("en", 3 * _FACTOR),
            ("es", 1),
            ("de", 2 * _FACTOR),
            ("zh", 4),
        ]
    )
    def test_fetch_top_news_rss(self, lang, top_n):
        """Unit test for fetch_top_news_rss."""
        news_items = fetcher.fetch_top_news_rss(lang=lang, top_n=top_n)
        self.assertIsInstance(news_items, list)
        self.assertLessEqual(len(news_items), top_n)
        logging.info("News in `%s` (# = %d --> %d):", lang, top_n, len(news_items))
        logging.info("%s\n\n", news_items)

        for item in news_items:
            self.assertIn("title", item)
            self.assertIsInstance(item["title"], str)
            self.assertTrue(len(item["title"]) > 0)

            self.assertIn("content", item)
            self.assertIsInstance(item["content"], str)

    def test__invalid_fetch_top_news_rss(self):
        """Unit test for fetch_top_news_rss."""
        with self.assertRaises(ValueError):
            fetcher.fetch_top_news_rss(lang="xx")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)
    unittest.main()
