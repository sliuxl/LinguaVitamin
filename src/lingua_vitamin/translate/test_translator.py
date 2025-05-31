"""Unit tests for translator.py."""

import logging
import unittest
from parameterized import parameterized

from lingua_vitamin.translate import translator


LOGGING_FORMAT = "%(asctime)s [%(filename)s:%(lineno)d] %(levelname)s - %(message)s"

TEXTS_DE = (
    "Guten Morgen! Wie geht es dir? Das Wetter ist heute sehr schön.",
    "Paris ist schön.",
    "Ich trinke gerne Kaffee am Morgen.",
)

TEXTS_EN = (
    "Good morning! How are you?",
    "The weather is very nice today.",
    "Paris is beautiful.",
)


class TestTranslator(unittest.TestCase):
    """Unit tests for translator.py."""

    @parameterized.expand(
        [
            # From de
            ("de", "en", TEXTS_DE),
            ("de", "es", TEXTS_DE[:1]),
            ("de", "fr", TEXTS_DE[:2]),
            ("de", "zh", TEXTS_DE),
            # From en
            ("en", "de", TEXTS_EN),
            ("en", "zh", TEXTS_EN),
        ]
    )
    def test_translate(self, src: str, target: str, texts):
        """Unit tests for translate."""
        translations = translator.Translator(src, target).translate(texts)

        logging.info("Translation `%s` -> `%s`", src, target)
        for x, y in zip(texts, translations):
            logging.info("%40s >>> %s", x, y)
        logging.info("\n\n")

        self.assertIsInstance(translations, list)
        self.assertEqual(len(translations), len(texts))
        for text in translations:
            self.assertIsInstance(text, str)
            self.assertGreater(len(text), 0)

    @parameterized.expand(
        [
            ("jp", "en"),
            ("en", "jp"),
        ]
    )
    def test_translate_invalid(self, src: str, target: str):
        """Unit tests for translate."""
        with self.assertRaises(ValueError):
            translator.Translator(src, target)

    _LONG = " ".join(str(i) for i in range(512))

    @parameterized.expand(
        [
            ("de", "en", _LONG),
            ("en", "de", _LONG),
        ]
    )
    def test_translate_none(self, src: str, target: str, text):
        """Unit tests for translate: None for long sequences."""
        self.assertIsNone(translator.Translator(src, target).translate((text,)))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)
    unittest.main()
