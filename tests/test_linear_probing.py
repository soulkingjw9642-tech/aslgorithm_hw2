import unittest

from src.linear_probing import LinearProbingHashTable


class LinearProbingHashTableTests(unittest.TestCase):
    def test_wraps_from_last_slot_and_resizes(self):
        table = LinearProbingHashTable(capacity=4, max_load_factor=1.0)
        table.put("c", "first")
        table.put("g", "second")

        self.assertEqual(table.get("g"), "second")
        self.assertEqual(table.last_lookup_slots, [3, 0])
        self.assertEqual(table.last_lookup_probes, 2)

        table.put("k", "third")
        table.put("o", "fourth")
        table.put("extra", "fifth")
        self.assertEqual(table.capacity, 8)
        for key, value in (
            ("c", "first"),
            ("g", "second"),
            ("k", "third"),
            ("o", "fourth"),
            ("extra", "fifth"),
        ):
            self.assertEqual(table.get(key), value)

    def test_handles_full_table_and_tombstones(self):
        table = LinearProbingHashTable(capacity=2, max_load_factor=None)
        table.put("a", "first")
        table.put("c", "second")

        with self.assertRaises(OverflowError):
            table.put("e", "third")

        table.delete("a")
        self.assertEqual(table.get("c"), "second")
        table.put("e", "third")
        self.assertEqual(table.get("e"), "third")
        self.assertEqual(len(table), 2)
        with self.assertRaises(KeyError):
            table.delete("missing")

    def test_overwrites_and_validates_types(self):
        table = LinearProbingHashTable()
        table.put("key", "old")
        table.put("key", "new")
        self.assertEqual(len(table), 1)
        self.assertEqual(table.get("key"), "new")

        with self.assertRaises(TypeError):
            table.put("other", 1)


if __name__ == "__main__":
    unittest.main()
