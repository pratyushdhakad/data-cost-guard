import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_cost_guard.analytics import detect_anomalies, forecast_month_end, validate_input
from data_cost_guard.generate_data import generate_synthetic_data


class AnalyticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / "artifacts" / "test_connector_costs.csv"
        generate_synthetic_data(cls.path)
        cls.frame = pd.read_csv(cls.path)

    @classmethod
    def tearDownClass(cls):
        cls.path.unlink(missing_ok=True)

    def test_generated_data_passes_validation(self):
        validate_input(self.frame)
        self.assertEqual(len(self.frame), 181 * 8)

    def test_known_spikes_are_detected(self):
        scored = detect_anomalies(self.frame)
        anomalies = scored[scored["is_anomaly"]]
        self.assertGreaterEqual(len(anomalies), 4)
        self.assertIn("subscription_events", set(anomalies["connector"]))

    def test_forecast_is_positive(self):
        forecast = forecast_month_end(self.frame)
        self.assertGreater(forecast["next_30_day_forecast_usd"], 0)

    def test_missing_columns_fail_fast(self):
        with self.assertRaisesRegex(ValueError, "Missing required columns"):
            validate_input(pd.DataFrame({"usage_date": ["2026-01-01"]}))


if __name__ == "__main__":
    unittest.main()
