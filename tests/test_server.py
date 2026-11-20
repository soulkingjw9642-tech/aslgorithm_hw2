import http.client
import threading
import unittest
from urllib.parse import urlencode

from src.server import ShortenerHTTPServer


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = ShortenerHTTPServer(("127.0.0.1", 0), "chaining")
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

    def test_linear_strategy_uses_slot_view(self):
        linear_server = ShortenerHTTPServer(("127.0.0.1", 0), "linear")
        linear_thread = threading.Thread(
            target=linear_server.serve_forever, daemon=True
        )
        linear_thread.start()
        connection = http.client.HTTPConnection(*linear_server.server_address)
        try:
            connection.request(
                "POST",
                "/",
                body=urlencode({"url": "https://example.com/linear"}),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            response.read()

            connection.request("GET", "/table")
            response = connection.getresponse()
            table_page = response.read()
            self.assertEqual(response.status, 200)
            self.assertIn(b"linear probing", table_page)
            self.assertIn(b"Slot 0", table_page)
            self.assertIn(b"lookup visited slots", table_page)
        finally:
            connection.close()
            linear_server.shutdown()
            linear_server.server_close()
            linear_thread.join()

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
