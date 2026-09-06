"""The Action draws a wall, not a bordered table."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FILL = ROOT / "fill.py"


def _load():
    spec = importlib.util.spec_from_file_location("readme_contributors_fill", FILL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FillTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = _load()

    def test_action_manifest_is_composite(self) -> None:
        text = (ROOT / "action.yml").read_text(encoding="utf-8")
        self.assertIn("using: composite", text)
        self.assertIn("fill.py", text)

    def test_svg_facepile_clips_to_a_circle(self) -> None:
        svg = self.mod.render_svg(
            [
                {"login": "alice", "name": "Alice Example"},
                {"login": "bob", "name": "Bob"},
            ],
            {"alice": self.mod.TINY_PNG},
        )
        self.assertIn('clip-path="url(#c0)"', svg)
        self.assertIn("data:image/png;base64,", svg)
        self.assertIn("hsl(", svg)
        self.assertNotIn("<table>", svg)

    def test_ninth_person_wraps_to_a_second_row(self) -> None:
        people = [{"login": f"u{i}", "name": f"User {i}"} for i in range(9)]
        svg = self.mod.render_svg(people, size=72, columns=8)
        self.assertIn('height="166"', svg)

    def test_html_mode_has_no_table(self) -> None:
        html = self.mod.render_wall(
            [{"login": "carol", "name": "Carol"}],
            format="html",
        )
        self.assertIn("github.com/carol", html)
        self.assertNotIn("<table>", html)

    def test_display_names_are_escaped(self) -> None:
        nasty = [{"login": "eve", "name": "<script>alert(1)</script>"}]
        html = self.mod.render_wall(nasty, format="html")
        svg = self.mod.render_svg(nasty)
        self.assertNotIn("<script>", html)
        self.assertNotIn("<script>", svg)
        self.assertIn("&lt;script&gt;", html)

    def test_apply_readme_replaces_only_the_marked_block(self) -> None:
        start = self.mod.DEFAULT_START
        end = self.mod.DEFAULT_END
        text = f"before\n{start}\nold\n{end}\nafter\n"
        out = self.mod.apply_readme(text, "new\n")
        self.assertEqual(out, f"before\n{start}\nnew\n{end}\nafter\n")

    def test_empty_list_is_a_blank_wall(self) -> None:
        self.assertEqual(self.mod.render_html([]), "")
        self.assertIn("<svg", self.mod.render_svg([]))

    def test_check_mode_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            start = self.mod.DEFAULT_START
            end = self.mod.DEFAULT_END
            readme.write_text(f"{start}\n{end}\n", encoding="utf-8")
            env = {
                "GITHUB_WORKSPACE": str(root),
                "GITHUB_REPOSITORY": "owner/name",
                "FORMAT": "html",
                "CHECK": "true",
            }
            old = {key: __import__("os").environ.get(key) for key in env}

            def people(_repo: str, _token: str, limit: int = 48):
                return [{"login": "alice", "name": "Alice"}]

            self.mod.list_people = people  # type: ignore[method-assign]
            try:
                for key, value in env.items():
                    __import__("os").environ[key] = value
                with mock.patch("sys.stdout", new=StringIO()):
                    code = self.mod.main()
            finally:
                for key, value in old.items():
                    if value is None:
                        __import__("os").environ.pop(key, None)
                    else:
                        __import__("os").environ[key] = value
            self.assertEqual(code, 1)
            self.assertEqual(readme.read_text(encoding="utf-8"), f"{start}\n{end}\n")
