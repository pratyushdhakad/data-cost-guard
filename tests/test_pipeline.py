import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_cost_guard.pipeline import run


class PipelineTests(unittest.TestCase):
    def test_pipeline_creates_public_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "sql").mkdir()
            (project / "sql" / "01_daily_connector_cost.sql").write_text(
                (ROOT / "sql" / "01_daily_connector_cost.sql").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            summary = run(project)
            self.assertTrue((project / "dashboard" / "index.html").exists())
            saved = json.loads((project / "artifacts" / "summary.json").read_text())
            self.assertEqual(saved["anomaly_count"], summary["anomaly_count"])


if __name__ == "__main__":
    unittest.main()
