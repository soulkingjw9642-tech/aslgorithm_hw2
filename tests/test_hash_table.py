import unittest

from src.hash_table import HashTable


class HashTableTests(unittest.TestCase):
    def test_collision_overwrite_and_missing_key(self):
        table = HashTable(capacity=8)
        table.put("a", "first")
        table.put("i", "second")

        self.assertEqual(len(table), 2)
        self.assertTrue(table.contains("a"))
        self.assertTrue(table.contains("i"))
        self.assertEqual(table.get("a"), "first")
        self.assertEqual(table.get("i"), "second")

        table.put("a", "updated")
        self.assertEqual(len(table), 2)
        self.assertEqual(table.get("a"), "updated")
        with self.assertRaises(KeyError):
            table.get("missing")

    def test_resizes_and_keeps_all_items(self):
        table = HashTable(capacity=2)
        for value in range(20):
            table.put(f"key-{value}", f"value-{value}")

        self.assertEqual(len(table), 20)
        for value in range(20):
            self.assertEqual(table.get(f"key-{value}"), f"value-{value}")

    def test_rejects_non_string_keys_and_values(self):
        table = HashTable()
        with self.assertRaises(TypeError):
            table.put(1, "value")
        with self.assertRaises(TypeError):
            table.put("key", 1)
        with self.assertRaises(TypeError):
            table.get(1)
        with self.assertRaises(TypeError):
            table.contains(1)


if __name__ == "__main__":
    unittest.main()
