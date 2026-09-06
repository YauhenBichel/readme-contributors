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

    def test_readme_has_a_live_demo(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("<!-- demo: live -start -->", text)
        self.assertIn("docs/demo.svg", text)
        self.assertTrue((ROOT / "docs" / "demo.svg").is_file())
        self.assertIn("<svg", (ROOT / "docs" / "demo.svg").read_text(encoding="utf-8"))
        self.assertIn("layout: tiles", text)
        self.assertIn("theme: midnight", text)
        self.assertIn("GitHub Action", text)
        self.assertIn("yauhenbichel.github.io/readme-contributors", text)
        self.assertIn("## Used by", text)
        self.assertIn("YauhenBichel/py-harness", text)
        self.assertIn("YauhenBichel/merge-cheer", text)
        self.assertIn("github.com/search?q=YauhenBichel%2Freadme-contributors", text)
        for name in (
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
            "theme-sunrise.svg",
            "theme-forest.svg",
            "theme-ocean.svg",
            "theme-mono.svg",
        ):
            path = ROOT / "docs" / name
            self.assertTrue(path.is_file(), name)
            self.assertIn("<svg", path.read_text(encoding="utf-8"))

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

    def test_grid_does_not_overlap_faces(self) -> None:
        people = [{"login": "alice", "name": "Alice"}, {"login": "bob", "name": "Bob"}]
        svg = self.mod.render_svg(people, layout="grid", size=72, columns=8)
        self.assertIn('cx="44.0"', svg)
        self.assertIn('cx="128.0"', svg)
        self.assertNotIn("<table>", svg)

    def test_tiles_use_rounded_rects(self) -> None:
        svg = self.mod.render_svg(
            [{"login": "alice", "name": "Alice"}],
            layout="tiles",
        )
        self.assertIn("<rect", svg)
        self.assertIn('rx="', svg)

    def test_list_writes_the_name_beside_the_face(self) -> None:
        svg = self.mod.render_svg(
            [{"login": "alice", "name": "Alice Example"}],
            layout="list",
        )
        self.assertIn("Alice Example", svg)
        self.assertIn("@alice", svg)

    def test_compact_is_tighter_than_grid(self) -> None:
        people = [{"login": f"u{i}", "name": f"User {i}"} for i in range(4)]
        grid = self.mod.svg_width(people, 72, 8, layout="grid")
        compact = self.mod.svg_width(people, 72, 8, layout="compact")
        self.assertLess(compact, grid)

    def test_midnight_theme_paints_a_dark_frame(self) -> None:
        svg = self.mod.render_svg(
            [{"login": "alice", "name": "Alice"}],
            theme="midnight",
        )
        self.assertIn("#0d1117", svg)
        self.assertIn("#e6edf3", svg)

    def test_wave_lifts_every_other_face(self) -> None:
        people = [{"login": f"u{i}", "name": f"User {i}"} for i in range(4)]
        svg = self.mod.render_svg(people, layout="wave", size=64, columns=8)
        self.assertIn('cy="', svg)
        first = svg.split('cy="', 1)[1].split('"', 1)[0]
        second = svg.split('cy="', 2)[2].split('"', 1)[0]
        self.assertNotEqual(first, second)

    def test_orbit_puts_one_person_in_the_middle(self) -> None:
        people = [{"login": f"u{i}", "name": f"User {i}"} for i in range(5)]
        svg = self.mod.render_svg(people, layout="orbit", size=48)
        self.assertIn('class="link"', svg)
        self.assertIn('r="26.5"', svg)
        self.assertIn('r="24.0"', svg)

    def test_honeycomb_clips_to_a_hex(self) -> None:
        svg = self.mod.render_svg(
            [{"login": "alice", "name": "Alice"}],
            layout="honeycomb",
        )
        self.assertIn("<polygon", svg)

    def test_ribbon_staggers_the_row(self) -> None:
        people = [{"login": "a", "name": "A"}, {"login": "b", "name": "B"}]
        svg = self.mod.render_svg(people, layout="ribbon", size=50)
        self.assertIn('cy="33.0"', svg)
        self.assertIn('cy="51.0"', svg)

    def test_constellation_draws_links(self) -> None:
        people = [{"login": f"u{i}", "name": f"User {i}"} for i in range(3)]
        svg = self.mod.render_svg(people, layout="constellation")
        self.assertIn("<line", svg)
        self.assertIn('class="link"', svg)

    def test_banner_enlarges_the_first_person(self) -> None:
        people = [{"login": "a", "name": "A"}, {"login": "b", "name": "B"}]
        svg = self.mod.render_svg(people, layout="banner", size=40)
        self.assertIn('r="31.0"', svg)
        self.assertIn('r="20.0"', svg)

    def test_unknown_layout_is_a_refusal(self) -> None:
        with self.assertRaises(SystemExit) as raised:
            self.mod.parse_layout("carousel")
        self.assertIn("facepile", str(raised.exception))

    def test_unknown_theme_is_a_refusal(self) -> None:
        with self.assertRaises(SystemExit) as raised:
            self.mod.parse_theme("neon")
        self.assertIn("midnight", str(raised.exception))

    def test_action_manifest_exposes_layout_and_theme(self) -> None:
        text = (ROOT / "action.yml").read_text(encoding="utf-8")
        self.assertIn("layout:", text)
        self.assertIn("theme:", text)
        self.assertIn("LAYOUT:", text)
        self.assertIn("THEME:", text)

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
