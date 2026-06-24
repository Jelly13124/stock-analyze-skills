import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "stock-analysis" / "scripts"))

from fetch_ownership import summarize_ownership  # noqa: E402


class TestSummarizeOwnership(unittest.TestCase):
    def test_retail_residual(self):
        out = summarize_ownership({"pct_held_institutions": 0.70, "pct_held_insiders": 0.10})
        self.assertAlmostEqual(out["pct_held_retail"], 0.20, places=6)

    def test_retail_floored_at_zero(self):
        out = summarize_ownership({"pct_held_institutions": 0.95, "pct_held_insiders": 0.10})
        self.assertEqual(out["pct_held_retail"], 0.0)

    def test_retail_none_when_missing(self):
        out = summarize_ownership({"pct_held_institutions": None, "pct_held_insiders": 0.10})
        self.assertIsNone(out["pct_held_retail"])

    def test_top10_concentration_sums_pct_out(self):
        raw = {"institutional_holders": [{"pct_out": 0.05}, {"pct_out": 0.03}, {"pct_out": None}]}
        out = summarize_ownership(raw)
        self.assertAlmostEqual(out["top10_concentration_pct"], 0.08, places=6)

    def test_top10_caps_at_ten(self):
        raw = {"institutional_holders": [{"pct_out": 0.01} for _ in range(15)]}
        out = summarize_ownership(raw)
        self.assertEqual(len(out["top10_institutional"]), 10)

    def test_top10_concentration_none_when_no_holders(self):
        out = summarize_ownership({})
        self.assertIsNone(out["top10_concentration_pct"])
        self.assertEqual(out["top10_institutional"], [])


if __name__ == "__main__":
    unittest.main()
