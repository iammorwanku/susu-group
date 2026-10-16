import io
import os
import tempfile
import unittest

from susu.cli import main


class CliTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.file = os.path.join(self.dir.name, "g.json")

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = main(["-f", self.file, *argv], out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def setup_group(self):
        self.assertEqual(self.run_cli("init", "--amount", "50.00")[0], 0)
        for name in ["Ama", "Kofi", "Esi"]:
            self.assertEqual(self.run_cli("add", name)[0], 0)

    def test_full_example_from_the_brief(self):
        self.setup_group()
        self.run_cli("pay", "Ama", "50")
        self.run_cli("pay", "Kofi", "50")
        code, out, _ = self.run_cli("pay", "Esi", "30")
        self.assertEqual(code, 0)
        self.assertIn("still owes GHS 20.00", out)

        code, out, _ = self.run_cli("close")
        self.assertEqual(code, 0)
        self.assertIn("cannot close", out)
        self.assertIn("Esi owes GHS 20.00", out)

        self.run_cli("pay", "Esi", "20")
        code, out, _ = self.run_cli("close")
        self.assertIn("Ama receives GHS 150.00", out)
        self.assertIn("Next recipient: Kofi", out)

        _, report, _ = self.run_cli("report")
        self.assertIn("Current week: 2 of 3", report)
        self.assertIn("Week 1: Ama received GHS 150.00", report)

    def test_state_persists_between_invocations(self):
        self.setup_group()
        self.run_cli("pay", "Esi", "12.50")
        _, report, _ = self.run_cli("report")
        self.assertIn("Esi owes GHS 37.50 (paid GHS 12.50)", report)

    def test_errors_are_reported_with_exit_code_1_and_change_nothing(self):
        self.setup_group()
        cases = [
            ("pay", "Yaw", "10"),             # unknown member
            ("pay", "Ama", "0"),              # zero
            ("pay", "Ama", "-5"),             # negative
            ("pay", "Ama", "50.01"),          # overpayment
            ("pay", "Ama", "abc"),            # not a number
            ("pay", "Ama", "1.005"),          # sub-pesewa precision
            ("add", "kofi"),                  # duplicate
            ("pay", "Ama", "5", "--week", "3"),  # wrong week
        ]
        for argv in cases:
            with self.subTest(argv=argv):
                code, out, err = self.run_cli(*argv)
                self.assertEqual(code, 1)
                self.assertTrue(err.startswith("Error:"))
        _, report, _ = self.run_cli("report")
        self.assertIn("Paid in full:\n  (nobody yet)", report)

    def test_cannot_add_member_after_payments_start(self):
        self.setup_group()
        self.run_cli("pay", "Ama", "1")
        code, _, err = self.run_cli("add", "Yaw")
        self.assertEqual(code, 1)
        self.assertIn("before the first contribution", err)

    def test_init_refuses_to_overwrite_without_force(self):
        self.setup_group()
        self.assertEqual(self.run_cli("init", "--amount", "10")[0], 1)
        self.assertEqual(self.run_cli("init", "--amount", "10", "--force")[0], 0)

    def test_commands_without_a_group_fail_cleanly(self):
        code, _, err = self.run_cli("report")
        self.assertEqual(code, 1)
        self.assertIn("No group found", err)


if __name__ == "__main__":
    unittest.main()
