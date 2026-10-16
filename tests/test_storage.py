import json
import os
import tempfile
import unittest

from susu import storage
from susu.errors import StorageError
from susu.group import Group
from susu.money import to_pesewas as p


def sample_group() -> Group:
    g = Group(p("50.00"))
    for n in ["Ama", "Kofi", "Esi"]:
        g.add_member(n)
    for n in g.members:
        g.record_contribution(n, p("50"))
    g.close_week()                       # Ama paid out, now week 2
    g.record_contribution("Kofi", p("12.34"))
    return g


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path = os.path.join(self.dir.name, "susu.json")

    def test_round_trip_preserves_everything_exactly(self):
        original = sample_group()
        storage.save(self.path, original)
        loaded = storage.load(self.path)
        self.assertEqual(storage.group_to_dict(loaded), storage.group_to_dict(original))
        self.assertEqual(loaded.week, 2)
        self.assertEqual(loaded.paid["Kofi"], p("12.34"))

    def test_missing_file_gives_helpful_error(self):
        with self.assertRaises(StorageError):
            storage.load(self.path)

    def test_invalid_json_is_a_storage_error(self):
        with open(self.path, "w") as f:
            f.write("{not json")
        with self.assertRaises(StorageError):
            storage.load(self.path)

    def test_tampered_data_is_rejected(self):
        storage.save(self.path, sample_group())
        with open(self.path) as f:
            data = json.load(f)
        data["paid"]["Kofi"] = 999999          # more than the weekly amount
        with open(self.path, "w") as f:
            json.dump(data, f)
        with self.assertRaises(StorageError):
            storage.load(self.path)


if __name__ == "__main__":
    unittest.main()
