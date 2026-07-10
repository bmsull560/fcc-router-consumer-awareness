import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestExportJson(unittest.TestCase):
    def test_exports_search_index_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(ROOT / 'scripts' / 'export_site_json.py'), '--out', tmp],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            path = Path(tmp) / 'search_index.json'
            self.assertTrue(path.exists())
            data = json.loads(path.read_text(encoding='utf-8'))
            self.assertIsInstance(data, list)
            if data:
                self.assertIn('table_name', data[0])
                self.assertIn('row_id', data[0])
                self.assertIn('title', data[0])
                self.assertIn('snippet', data[0])

    def test_export_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            subprocess.run([sys.executable, str(ROOT / 'scripts' / 'export_site_json.py'), '--out', tmp1], check=True)
            subprocess.run([sys.executable, str(ROOT / 'scripts' / 'export_site_json.py'), '--out', tmp2], check=True)
            for name in ['current_status.json', 'faqs.json', 'timeline.json', 'search_index.json']:
                a = Path(tmp1) / name
                b = Path(tmp2) / name
                self.assertEqual(a.read_bytes(), b.read_bytes(), f'{name} differs')
