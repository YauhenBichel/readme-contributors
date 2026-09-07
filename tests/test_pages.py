"""The GitHub Pages site is a how-to, not an essay."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs" / "index.html"


class PagesTest(unittest.TestCase):
    def test_site_explains_how_to_use_the_action(self) -> None:
        text = SITE.read_text(encoding="utf-8")
        self.assertIn("uses: YauhenBichel/readme-contributors@v1.6.0", text)
        self.assertIn("&lt;!-- readme: contributors,bots/- -start --&gt;", text)
        self.assertIn("layout: stickers", text)
        self.assertIn("layout: orbit", text)
        self.assertIn("layout: honeycomb", text)
        self.assertIn("theme: midnight", text)
        self.assertIn("id=\"used-by\"", text)
        self.assertIn("id=\"live\"", text)
        self.assertIn("id=\"what\"", text)
        self.assertIn("id=\"why\"", text)
        self.assertIn("id=\"demo\"", text)
        self.assertIn("./media/readme-contributors-demo.mp4", text)
        self.assertIn("./faces/YauhenBichel.svg", text)
        self.assertIn('href="https://github.com/YauhenBichel"', text)
        self.assertIn("github.com/YauhenBichel/py-harness", text)
        self.assertIn("github.com/YauhenBichel/merge-cheer", text)
        self.assertIn("marketplace/actions/readme-contributors", text)
        self.assertIn("github.com/MoleCare/molecare-mcp", text)
        self.assertNotIn("/Users/", text)
        self.assertNotIn("DevBox", text)
        self.assertNotIn("webfont", text.lower())
        self.assertNotIn("<script", text.lower())

    def test_every_layout_picture_exists(self) -> None:
        text = SITE.read_text(encoding="utf-8")
        for name in (
            "demo.svg",
            "layout-facepile.svg",
            "layout-stickers.svg",
            "layout-grid.svg",
            "layout-tiles.svg",
            "layout-list.svg",
            "layout-compact.svg",
            "layout-wave.svg",
            "layout-orbit.svg",
            "layout-honeycomb.svg",
            "layout-ribbon.svg",
            "layout-constellation.svg",
            "layout-banner.svg",
            "theme-midnight.svg",
            "faces/YauhenBichel.svg",
            "faces/xianjianlf2.svg",
            "faces/ItzSaurav.svg",
            "faces/svkzn.svg",
            "faces/Aditya-233.svg",
            "faces/kkkhs.svg",
        ):
            self.assertIn(f"./{name}", text)
            path = ROOT / "docs" / name
            self.assertTrue(path.is_file(), name)
            self.assertIn("<svg", path.read_text(encoding="utf-8"))

    def test_pages_workflow_publishes_the_docs_folder(self) -> None:
        text = (ROOT / ".github" / "workflows" / "pages.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("docs/index.html", text)
        self.assertIn("docs/faces", text)
        self.assertIn("docs/media", text)
        self.assertIn("pages: write", text)
        self.assertTrue((ROOT / "docs" / ".nojekyll").is_file())
        self.assertTrue((ROOT / "docs" / "media" / "readme-contributors-demo.mp4").is_file())
        self.assertTrue((ROOT / "docs" / "media" / "demo-poster.png").is_file())
