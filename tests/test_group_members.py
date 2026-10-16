import unittest

from susu.errors import DuplicateMember, InvalidAmount, InvalidName
from susu.group import Group
from susu.money import to_pesewas as p


class CreateGroupTests(unittest.TestCase):
    def test_creates_with_weekly_amount(self):
        g = Group(p("50.00"))
        self.assertEqual(g.weekly_amount, 5000)
        self.assertEqual(g.week, 1)
        self.assertEqual(g.members, [])

    def test_rejects_zero_negative_and_non_int_amounts(self):
        for bad in [0, -100, 50.0, True, "50"]:
            with self.subTest(bad=bad):
                with self.assertRaises(InvalidAmount):
                    Group(bad)


class AddMemberTests(unittest.TestCase):
    def test_members_keep_joining_order(self):
        g = Group(p("50"))
        for name in ["Ama", "Kofi", "Esi"]:
            g.add_member(name)
        self.assertEqual(g.members, ["Ama", "Kofi", "Esi"])

    def test_duplicate_is_rejected_ignoring_case_and_spacing(self):
        g = Group(p("50"))
        g.add_member("Ama Mensah")
        for dup in ["Ama Mensah", "ama mensah", "  AMA   mensah "]:
            with self.subTest(dup=dup):
                with self.assertRaises(DuplicateMember):
                    g.add_member(dup)
        self.assertEqual(g.members, ["Ama Mensah"])

    def test_blank_or_overlong_names_are_rejected(self):
        g = Group(p("50"))
        with self.assertRaises(InvalidName):
            g.add_member("   ")
        with self.assertRaises(InvalidName):
            g.add_member("x" * 51)


if __name__ == "__main__":
    unittest.main()
