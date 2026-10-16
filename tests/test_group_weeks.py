import unittest

from susu.errors import (
    GroupComplete,
    InvalidAmount,
    MembersLocked,
    NotEnoughMembers,
    Overpayment,
    UnknownMember,
    WrongWeek,
)
from susu.group import Group
from susu.money import to_pesewas as p


def make_group(names=("Ama", "Kofi", "Esi"), amount="50.00") -> Group:
    g = Group(p(amount))
    for n in names:
        g.add_member(n)
    return g


def everyone_pays(g: Group) -> None:
    for name, owed in g.outstanding().items():
        g.record_contribution(name, owed)


class SpecExampleTest(unittest.TestCase):
    def test_example_from_the_brief(self):
        g = make_group()
        g.record_contribution("Ama", p("50"))
        g.record_contribution("Kofi", p("50"))
        g.record_contribution("Esi", p("30"))

        result = g.close_week()
        self.assertFalse(result.closed)
        self.assertEqual(result.owing, {"Esi": p("20")})
        self.assertEqual(g.payouts, [])
        self.assertEqual(g.week, 1)

        g.record_contribution("Esi", p("20"))
        result = g.close_week()
        self.assertTrue(result.closed)
        self.assertEqual((result.payout.member, result.payout.amount), ("Ama", p("150")))
        self.assertEqual(g.week, 2)
        self.assertEqual(g.next_recipient, "Kofi")


class PartialPaymentTests(unittest.TestCase):
    def test_partial_payments_accumulate_and_report_remaining(self):
        g = make_group()
        self.assertEqual(g.record_contribution("Esi", p("30")), p("20"))
        self.assertEqual(g.amount_owed("Esi"), p("20"))
        self.assertEqual(g.record_contribution("Esi", p("19.99")), 1)  # 0.01 left
        self.assertEqual(g.record_contribution("Esi", 1), 0)
        self.assertEqual(g.amount_owed("Esi"), 0)

    def test_lookup_is_case_insensitive(self):
        g = make_group()
        g.record_contribution("  esi ", p("10"))
        self.assertEqual(g.amount_owed("Esi"), p("40"))


class CloseWeekTests(unittest.TestCase):
    def test_week_cannot_close_when_someone_has_not_paid(self):
        g = make_group()
        g.record_contribution("Ama", p("50"))
        result = g.close_week()
        self.assertFalse(result.closed)
        self.assertEqual(result.owing, {"Kofi": p("50"), "Esi": p("50")})
        self.assertEqual(g.week, 1)
        self.assertEqual(g.payouts, [])
        self.assertEqual(g.paid["Ama"], p("50"))  # payments are kept

    def test_payouts_follow_joining_order_and_pot_is_exact(self):
        g = make_group(("Ama", "Kofi", "Esi"), amount="33.33")
        for expected in ["Ama", "Kofi", "Esi"]:
            everyone_pays(g)
            result = g.close_week()
            self.assertTrue(result.closed)
            self.assertEqual(result.payout.member, expected)
            self.assertEqual(result.payout.amount, 3 * p("33.33"))
        self.assertEqual([x.week for x in g.payouts], [1, 2, 3])

    def test_new_week_starts_with_clean_balances(self):
        g = make_group()
        everyone_pays(g)
        g.close_week()
        self.assertEqual(g.outstanding(), {m: p("50") for m in g.members})

    def test_cycle_completes_and_then_refuses_activity(self):
        g = make_group(("Ama", "Kofi"))
        for _ in range(2):
            everyone_pays(g)
            g.close_week()
        self.assertTrue(g.is_complete)
        self.assertIsNone(g.next_recipient)
        with self.assertRaises(GroupComplete):
            g.close_week()
        with self.assertRaises(GroupComplete):
            g.record_contribution("Ama", p("1"))


class ValidationTests(unittest.TestCase):
    def test_unknown_member_rejected(self):
        g = make_group()
        with self.assertRaises(UnknownMember):
            g.record_contribution("Yaw", p("10"))

    def test_zero_and_negative_amounts_rejected(self):
        g = make_group()
        for bad in [0, -1, -5000]:
            with self.subTest(bad=bad):
                with self.assertRaises(InvalidAmount):
                    g.record_contribution("Ama", bad)

    def test_float_amount_rejected(self):
        g = make_group()
        with self.assertRaises(InvalidAmount):
            g.record_contribution("Ama", 10.5)

    def test_overpayment_rejected_single_cumulative_and_when_already_paid(self):
        g = make_group()
        with self.assertRaises(Overpayment):
            g.record_contribution("Ama", p("50.01"))
        g.record_contribution("Ama", p("30"))
        with self.assertRaises(Overpayment):
            g.record_contribution("Ama", p("20.01"))
        g.record_contribution("Ama", p("20"))
        with self.assertRaises(Overpayment):
            g.record_contribution("Ama", 1)
        self.assertEqual(g.paid["Ama"], p("50"))

    def test_rejected_payment_changes_nothing(self):
        g = make_group()
        g.record_contribution("Ama", p("10"))
        before = dict(g.paid)
        with self.assertRaises(Overpayment):
            g.record_contribution("Ama", p("100"))
        self.assertEqual(g.paid, before)

    def test_only_current_week_accepts_contributions(self):
        g = make_group()
        g.record_contribution("Ama", p("5"), week=1)
        for wrong in [0, 2, 99]:
            with self.assertRaises(WrongWeek):
                g.record_contribution("Ama", p("5"), week=wrong)

    def test_needs_two_members_to_take_payments_or_close(self):
        g = make_group(("Ama",))
        with self.assertRaises(NotEnoughMembers):
            g.record_contribution("Ama", p("10"))
        with self.assertRaises(NotEnoughMembers):
            g.close_week()


class MembersLockedTests(unittest.TestCase):
    def test_cannot_add_members_after_first_contribution(self):
        g = make_group()
        g.record_contribution("Ama", p("1"))
        with self.assertRaises(MembersLocked):
            g.add_member("Yaw")
        self.assertEqual(g.members, ["Ama", "Kofi", "Esi"])

    def test_cannot_add_members_after_a_payout(self):
        g = make_group()
        everyone_pays(g)
        g.close_week()
        with self.assertRaises(MembersLocked):
            g.add_member("Yaw")


if __name__ == "__main__":
    unittest.main()
