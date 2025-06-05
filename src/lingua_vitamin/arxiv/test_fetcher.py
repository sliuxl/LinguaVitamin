"""Unit tests for fetcher.py."""

import datetime
import logging
import unittest

import pandas as pd
from parameterized import parameterized

from lingua_vitamin.arxiv import fetcher


_DATE = datetime.datetime.today() - datetime.timedelta(days=7)
_DATE = f"{_DATE.year:04d}{_DATE.month:02d}{_DATE.day:02d}"

LOGGING_FORMAT = "%(asctime)s [%(filename)s:%(lineno)d] %(levelname)s - %(message)s"


class TestFetcher(unittest.TestCase):
    """Unit tests for fetcher.py."""

    @parameterized.expand(
        (
            (
                "cs.DC",
                _DATE,
                {},
            ),
            (
                "cs.DC",
                _DATE,
                {
                    "top_n": 1,
                },
            ),
            (
                "cs.PL",
                _DATE,
                {},
            ),
            (
                "hacker-news",
                _DATE,
                {},
            ),
        )
    )
    def test_fetch_arxiv_papers(self, subject, date, kwargs):
        """Unit test for fetch_arxiv_papers."""
        papers = fetcher.fetch_arxiv_papers(subject=subject, date=date, **kwargs)
        pd.DataFrame(papers).to_csv(f"/tmp/{subject}.csv")

        self.assertIsInstance(papers, list)
        logging.info("Papers in `%s` (# = %s --> %d):", subject, kwargs, len(papers))
        logging.info("%s\n\n", papers)

        for item in papers:
            self.assertEqual(len(item), 5)

            self.assertIn("title", item)
            self.assertIsInstance(item["title"], str)
            self.assertTrue(len(item["title"]) > 0)

            self.assertIn("abstract", item)
            self.assertIsInstance(item["abstract"], str)

            self.assertIn("date", item)
            self.assertIsInstance(item["date"], str)

            self.assertIn("url", item)
            self.assertIsInstance(item["url"], str)

            self.assertIn("authors", item)
            self.assertIsInstance(item["authors"], str)

            for key in ("abstract", "title"):
                self.assertNotIn("\n", item[key])

    def test_invalid_fetch_arxiv_papers(self):
        """Unit test for fetch_arxiv_papers."""
        self.assertEqual(fetcher.fetch_arxiv_papers(subject="xx", date=_DATE), [])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)
    unittest.main()
