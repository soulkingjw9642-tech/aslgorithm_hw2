"""URL shortening backed by a pluggable string hash table."""

from urllib.parse import urlsplit

from src.base62 import encode
from src.hash_table import HashTable


class Shortener:
    def __init__(self, table: HashTable | None = None) -> None:
        self._urls = table if table is not None else HashTable()
        self._codes = type(self._urls)()
        self._next_id = 0

    def shorten(self, url: str) -> str:
        self._validate_url(url)
        if self._urls.contains(url):
            return self._urls.get(url)

        code = encode(self._next_id)
        self._next_id += 1
        self._urls.put(url, code)
        self._codes.put(code, url)
        return code

    def expand(self, code: str) -> str:
        return self._codes.get(code)

    @staticmethod
    def _validate_url(url: str) -> None:
        if not isinstance(url, str):
            raise TypeError("url must be a string")
        if not url or any(
            ord(character) <= 0x20 or ord(character) == 0x7F for character in url
        ):
            raise ValueError(
                "url must not be empty or contain whitespace or control characters"
            )
        try:
            parsed = urlsplit(url)
            hostname = parsed.hostname
            parsed.port
        except ValueError as exc:
            raise ValueError("url must be a valid absolute HTTP(S) URL") from exc
        if parsed.scheme not in ("http", "https") or not hostname:
            raise ValueError("url must be a valid absolute HTTP(S) URL")
