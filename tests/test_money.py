import unittest

from susu.errors import InvalidAmount
from susu.money import format_pesewas, to_pesewas


class ToPesewasTests(unittest.TestCase):
    def test_parses_common_formats(self):
        self.assertEqual(to_pesewas("50"), 5000)
        self.assertEqual(to_pesewas("50.00"), 5000)
        self.assertEqual(to_pesewas("0.10"), 10)
        self.assertEqual(to_pesewas("1234.5"), 123450)
        self.assertEqual(to_pesewas(" 7.05 "), 705)

    def test_rejects_malformed_text(self):
        for bad in ["", "abc", "1.234", "1e2", "--5", "5.", ".5", "1,000", "NaN"]:
            with self.subTest(bad=bad):
                with self.assertRaises(InvalidAmount):
                    to_pesewas(bad)

    def test_rejects_floats_and_bools(self):
        with self.assertRaises(InvalidAmount):
            to_pesewas(0.1)
        with self.assertRaises(InvalidAmount):
            to_pesewas(True)

    def test_no_floating_point_drift(self):
        # 0.1 + 0.2 != 0.3 with floats; with pesewas it is exact.
        self.assertEqual(to_pesewas("0.10") + to_pesewas("0.20"), to_pesewas("0.30"))


class FormatPesewasTests(unittest.TestCase):
    def test_formats_two_decimals(self):
        self.assertEqual(format_pesewas(15000), "150.00")
        self.assertEqual(format_pesewas(5), "0.05")
        self.assertEqual(format_pesewas(0), "0.00")
        self.assertEqual(format_pesewas(-250), "-2.50")

    def test_round_trip(self):
        for text in ["0.01", "19.99", "50.00", "123456.78"]:
            self.assertEqual(format_pesewas(to_pesewas(text)), text)


if __name__ == "__main__":
    unittest.main()
