import http.client
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.parse import urlencode

from src.hash_table import HashTable
from src.server import ShortenerHandler
from src.shortener import Shortener


class TestShortenerHandler(ShortenerHandler):
    table = HashTable()
    shortener = Shortener(table)


class ServerTests(unittest.TestCase):
    def setUp(self):
        TestShortenerHandler.table = HashTable()
        TestShortenerHandler.shortener = Shortener(TestShortenerHandler.table)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), TestShortenerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.connection = http.client.HTTPConnection(*self.server.server_address)

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_form_create_redirect_and_table_details(self):
        self.connection.request("GET", "/")
        response = self.connection.getresponse()
        self.assertEqual(response.status, 200)
        self.assertIn(b'name="url"', response.read())

        url = "https://example.com/path"
        self.connection.request(
            "POST",
            "/",
            body=urlencode({"url": url}),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = self.connection.getresponse()
        self.assertEqual(response.status, 200)
        self.assertIn(b"/r/0", response.read())

        self.connection.request("GET", "/r/0")
        response = self.connection.getresponse()
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader("Location"), url)
        response.read()

        self.connection.request("GET", "/table")
        response = self.connection.getresponse()
        table_page = response.read()
        self.assertEqual(response.status, 200)
        self.assertIn(b"hash steps", table_page)
        self.assertIn(b"ord(", table_page)
        self.assertIn(b"lookup visited", table_page)
        self.assertIn(b"https://example.com/path", table_page)

    def test_invalid_url_and_unknown_code_return_errors(self):
        self.connection.request(
            "POST",
            "/",
            body=urlencode({"url": "ftp://example.com"}),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = self.connection.getresponse()
        self.assertEqual(response.status, 400)
        response.read()

        self.connection.request("GET", "/r/unknown")
        response = self.connection.getresponse()
        self.assertEqual(response.status, 404)
        response.read()


if __name__ == "__main__":
    unittest.main()
