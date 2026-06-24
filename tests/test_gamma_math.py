import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "stock-analysis" / "scripts"))

from gamma_math import bs_gamma, contract_gex, find_gamma_flip, gamma_wall, max_pain, net_gex_at  # noqa: E402


class TestContractGex(unittest.TestCase):
    def test_call_positive_put_negative(self):
        self.assertGreater(contract_gex(100, 100, 0.25, 0.30, 1000, "call"), 0.0)
        self.assertLess(contract_gex(100, 100, 0.25, 0.30, 1000, "put"), 0.0)


class TestBSGamma(unittest.TestCase):
    def test_positive_atm(self):
        self.assertGreater(bs_gamma(100, 100, 0.25, 0.30), 0.0)

    def test_atm_exceeds_far_otm(self):
        self.assertGreater(bs_gamma(100, 100, 0.25, 0.30), bs_gamma(100, 140, 0.25, 0.30))

    def test_degenerate_inputs_zero(self):
        self.assertEqual(bs_gamma(100, 100, 0.0, 0.30), 0.0)
        self.assertEqual(bs_gamma(100, 100, 0.25, 0.0), 0.0)
        self.assertEqual(bs_gamma(0, 100, 0.25, 0.30), 0.0)


class TestNetGex(unittest.TestCase):
    def test_calls_positive_puts_negative(self):
        calls = [{"strike": 100, "t_years": 0.25, "iv": 0.30, "oi": 1000, "kind": "call"}]
        puts = [{"strike": 100, "t_years": 0.25, "iv": 0.30, "oi": 1000, "kind": "put"}]
        self.assertGreater(net_gex_at(100, calls), 0.0)
        self.assertLess(net_gex_at(100, puts), 0.0)


class TestGammaFlip(unittest.TestCase):
    def test_flip_between_put_and_call_clusters(self):
        contracts = [
            {"strike": 90, "t_years": 0.25, "iv": 0.30, "oi": 5000, "kind": "put"},
            {"strike": 110, "t_years": 0.25, "iv": 0.30, "oi": 5000, "kind": "call"},
        ]
        flip = find_gamma_flip(contracts, 70, 130, steps=400)
        self.assertIsNotNone(flip)
        self.assertTrue(70 < flip < 130)

    def test_no_crossing_returns_none(self):
        contracts = [{"strike": 100, "t_years": 0.25, "iv": 0.30, "oi": 1000, "kind": "call"}]
        self.assertIsNone(find_gamma_flip(contracts, 80, 120))


class TestMaxPain(unittest.TestCase):
    def test_pain_minimized_at_heavy_oi_strike(self):
        calls = {90: 100, 100: 5000, 110: 100}
        puts = {90: 100, 100: 5000, 110: 100}
        self.assertEqual(max_pain(calls, puts), 100)

    def test_empty_none(self):
        self.assertIsNone(max_pain({}, {}))


class TestGammaWall(unittest.TestCase):
    def test_call_wall_at_highest_gamma_oi(self):
        contracts = [
            {"strike": 100, "t_years": 0.25, "iv": 0.30, "oi": 100, "kind": "call"},
            {"strike": 105, "t_years": 0.25, "iv": 0.30, "oi": 9000, "kind": "call"},
        ]
        self.assertEqual(gamma_wall(contracts, "call", 100), 105)

    def test_put_wall_and_missing_kind(self):
        contracts = [
            {"strike": 95, "t_years": 0.25, "iv": 0.30, "oi": 8000, "kind": "put"},
            {"strike": 90, "t_years": 0.25, "iv": 0.30, "oi": 100, "kind": "put"},
        ]
        self.assertEqual(gamma_wall(contracts, "put", 100), 95)
        self.assertIsNone(gamma_wall(contracts, "call", 100))


if __name__ == "__main__":
    unittest.main()
