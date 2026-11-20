import unittest

from src.hash_table import HashTable
from src.shortener import Shortener


class ShortenerTests(unittest.TestCase):
    def test_shortens_expands_and_reuses_urls(self):
        shortener = Shortener(HashTable())

        code = shortener.shorten("https://example.com/a?b=c")

        self.assertEqual(code, "0")
        self.assertEqual(shortener.expand(code), "https://example.com/a?b=c")
        self.assertEqual(shortener.shorten("https://example.com/a?b=c"), code)

    def test_rejects_invalid_urls_and_unknown_codes(self):
        shortener = Shortener(HashTable())
        for url in (
            " http://example.com",
            "ftp://example.com",
            "http:///missing-host",
            "https://",
            "https://example.com/a b",
            "https://example.com/\r\nInjected: header",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                shortener.shorten(url)

        with self.assertRaises(KeyError):
            shortener.expand("unknown")


if __name__ == "__main__":
    unittest.main()
