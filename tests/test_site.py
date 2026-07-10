import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestSiteAssets(unittest.TestCase):
    def test_style_css_exists(self):
        self.assertTrue((ROOT / 'site' / 'static' / 'style.css').exists())
