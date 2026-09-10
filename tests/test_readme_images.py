"""Every picture the README points at has to exist.

This repository sells avatar walls, and its README is the shop window: the
Marketplace listing renders this same file. A broken image here is the product
failing in public.

It happened. The workflow ran the Action twice against one faces folder, once
for the live demo and once for this repository's own wall. The second run
deletes faces for logins that have left the wall, which took five of the demo's
six with them, so the demo rendered as broken-image icons on the repo page and
on the Marketplace listing. The two walls have separate folders now, and this
test is what notices if they ever share one again.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# src="..." in HTML blocks and ![alt](path) in markdown. Remote URLs and
# fragments are somebody else's problem; only local paths are checked.
_HTML_SRC = re.compile(r'src="([^"]+)"')
_MD_IMAGE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")


def _local_paths(text: str) -> list[str]:
    found = _HTML_SRC.findall(text) + _MD_IMAGE.findall(text)
    return [
        p
        for p in found
        if not p.startswith(("http://", "https://", "data:", "#", "mailto:"))
    ]


class ReadmeImagesTest(unittest.TestCase):
    def test_every_local_image_in_the_readme_exists(self) -> None:
        readme = ROOT / "README.md"
        missing = [p for p in _local_paths(readme.read_text()) if not (ROOT / p).exists()]
        self.assertEqual(missing, [], f"README points at files that do not exist: {missing}")

    def test_the_two_walls_do_not_share_a_faces_folder(self) -> None:
        """The demo wall and this repository's wall prune each other otherwise."""
        workflow = (ROOT / ".github/workflows/contributors.yml").read_text()
        # The demo step must name a folder of its own; the default is
        # .github/faces, which is what the second step owns.
        self.assertIn("faces: docs/faces", workflow)

    def test_the_committed_faces_are_the_ones_the_readme_uses(self) -> None:
        """A face nothing points at is a leftover; catch it before it rots."""
        used = {p for p in _local_paths((ROOT / "README.md").read_text()) if "faces/" in p}
        for folder in ("docs/faces", ".github/faces"):
            for svg in (ROOT / folder).glob("*.svg"):
                rel = svg.relative_to(ROOT).as_posix()
                self.assertIn(rel, used, f"{rel} is committed but nothing in the README uses it")


if __name__ == "__main__":
    unittest.main()
