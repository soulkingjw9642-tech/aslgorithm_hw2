import unittest

from src.base62 import decode, encode


class Base62Tests(unittest.TestCase):
    def test_encodes_zero_and_alphabet_boundaries(self):
        self.assertEqual(encode(0), "0")
        self.assertEqual(encode(61), "Z")
        self.assertEqual(encode(62), "10")

    def test_round_trips_non_negative_integers(self):
        for value in (1, 12345, 2**64):
            with self.subTest(value=value):
                self.assertEqual(decode(encode(value)), value)

    def test_rejects_negative_values_and_invalid_codes(self):
        with self.assertRaises(ValueError):
            encode(-1)
        with self.assertRaises(ValueError):
            decode("")
        with self.assertRaises(ValueError):
            decode("a!")


if __name__ == "__main__":
    unittest.main()
