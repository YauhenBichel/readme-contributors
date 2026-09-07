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
        self.assertIn('href="https://github.com/YauhenBichel"', text)
        self.assertIn(".github/faces/YauhenBichel.svg", text)
        self.assertTrue((ROOT / "docs" / "demo.svg").is_file())
        self.assertIn("<svg", (ROOT / "docs" / "demo.svg").read_text(encoding="utf-8"))
        self.assertIn("layout: tiles", text)
        self.assertIn("theme: midnight", text)
        self.assertIn("GitHub Action", text)
        self.assertIn("yauhenbichel.github.io/readme-contributors", text)
        self.assertIn("## What", text)
        self.assertIn("## Why", text)
        self.assertIn("## How", text)
        self.assertIn("### Keep credits low", text)
        self.assertIn("readme-contributors-ai-demo.gif", text)
        self.assertIn("The wall is still the people who committed", text)
        self.assertIn("## Examples", text)
        self.assertIn("## Used by", text)
        self.assertIn("YauhenBichel/py-harness", text)
        self.assertIn("MoleCare/molecare-mcp", text)
        self.assertIn("#demo", text)
        self.assertIn("./docs/media/readme-contributors-demo.gif", text)
        self.assertTrue((ROOT / "docs" / "media" / "readme-contributors-demo.gif").is_file())
        self.assertIn("YauhenBichel/merge-cheer", text)
        self.assertIn("github.com/search?q=YauhenBichel%2Freadme-contributors", text)
        for name in (
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

    def test_stickers_tilt_the_faces(self) -> None:
        people = [{"login": "alice", "name": "Alice"}, {"login": "bob", "name": "Bob"}]
        svg = self.mod.render_svg(people, layout="stickers", size=64)
        self.assertIn('filter="url(#lift)"', svg)
        self.assertIn("rotate(-9", svg)
        self.assertIn("rotate(7", svg)
        self.assertIn("hsl(", svg)

    def test_polaroid_has_a_name_on_the_card(self) -> None:
        svg = self.mod.render_sticker_svg(
            {"login": "alice", "name": "Alice Example"},
            self.mod.TINY_PNG,
            tilt=-9,
        )
        self.assertIn("Alice Example", svg)
        self.assertIn("rotate(-9", svg)
        self.assertIn("#fffdf8", svg)
        self.assertIn("data:image/png;base64,", svg)

    def test_long_sticker_name_is_shortened(self) -> None:
        svg = self.mod.render_sticker_svg(
            {"login": "alice", "name": "A Very Long Display Name"}
        )
        self.assertIn(">A Very Long…</text>", svg)

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
        self.assertIn("FACES_PATH:", text)

    def test_html_mode_has_no_table(self) -> None:
        html = self.mod.render_wall(
            [{"login": "carol", "name": "Carol"}],
            format="html",
        )
        self.assertIn("github.com/carol", html)
        self.assertNotIn("<table>", html)

    def test_auto_layout_grows_with_the_list(self) -> None:
        self.assertEqual(self.mod.fit_layout("auto", 6), "facepile")
        self.assertEqual(self.mod.fit_layout("auto", 20), "grid")
        self.assertEqual(self.mod.fit_layout("auto", 50), "compact")
        self.assertEqual(self.mod.fit_layout("auto", 100), "compact")
        self.assertEqual(self.mod.fit_layout("orbit", 100), "orbit")

    def test_readme_faces_shrink_for_long_lists(self) -> None:
        self.assertEqual(self.mod.fit_readme_size(8, 72), 72)
        self.assertEqual(self.mod.fit_readme_size(20, 72), 72)
        self.assertEqual(self.mod.fit_readme_size(50, 72), 48)
        self.assertEqual(self.mod.fit_readme_size(100, 72), 36)

    def test_long_readme_wall_credits_every_name(self) -> None:
        people = [{"login": f"user{i}", "name": f"User {i}"} for i in range(20)]
        html = self.mod.render_wall(people)
        for person in people:
            self.assertIn(f'href="https://github.com/{person["login"]}"', html)
        self.assertIn("<span> · </span>", html)
        self.assertNotIn("<table>", html)

    def test_fifty_and_one_hundred_people_all_get_a_link(self) -> None:
        for count in (50, 100):
            people = [{"login": f"u{i}", "name": f"N{i}"} for i in range(count)]
            html = self.mod.render_wall(people)
            with self.subTest(count=count):
                self.assertEqual(
                    html.count('href="https://github.com/'), count * 2
                )


    def test_every_svg_face_links_to_the_profile(self) -> None:
        people = [
            {"login": "alice", "name": "Alice Example"},
            {"login": "bob", "name": "Bob"},
        ]
        svg = self.mod.render_svg(people, {"alice": self.mod.TINY_PNG})
        self.assertIn('<a href="https://github.com/alice" target="_top">', svg)
        self.assertIn('<a href="https://github.com/bob" target="_top">', svg)
        alice = svg.split('<a href="https://github.com/alice"', 1)[1].split(
            "</a>", 1
        )[0]
        self.assertIn("clip-path", alice)
        bob = svg.split('<a href="https://github.com/bob"', 1)[1].split("</a>", 1)[0]
        self.assertIn("hsl(", bob)

    def test_readme_icons_are_profile_links(self) -> None:
        people = [
            {"login": "alice", "name": "Alice"},
            {"login": "bob", "name": "Bob"},
        ]
        html = self.mod.render_wall(
            people,
            svg_href=".github/contributors.svg",
            svg_width=200,
            format="svg",
        )
        self.assertIn(
            '<a href="https://github.com/alice" title="Alice" aria-label="Alice">',
            html,
        )
        self.assertIn(
            'src="https://avatars.githubusercontent.com/alice?s=174"', html
        )
        self.assertIn(
            '<a href="https://github.com/bob" title="Bob" aria-label="Bob">',
            html,
        )
        self.assertIn('width="87"', html)
        self.assertIn('width="66"', html)
        self.assertEqual(html.count('<a href="https://github.com/'), 2)
        self.assertNotIn("contributors.svg", html)
        self.assertNotIn("<table>", html)
        self.assertNotIn("<br", html)

    def test_readme_icons_can_use_polaroid_files(self) -> None:
        html = self.mod.render_wall(
            [{"login": "alice", "name": "Alice"}],
            faces_href=".github/faces",
        )
        self.assertIn('src=".github/faces/alice.svg"', html)
        self.assertIn('href="https://github.com/alice"', html)

    def test_contributors_workflow_opens_a_pull_request(self) -> None:
        text = (ROOT / ".github" / "workflows" / "contributors.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("gh pr create", text)
        self.assertIn("gh pr merge", text)
        self.assertIn('gh pr merge "$NUMBER" --squash --auto || gh pr merge "$NUMBER" --squash', text)
        self.assertNotIn("--jq .number", text)
        self.assertIn("pull-requests: write", text)
        self.assertIn("format: html", text)
        self.assertIn("caption: auto", text)
        self.assertIn("secrets.OPENAI_API_KEY", text)
        self.assertIn(".github/faces", text)
        self.assertNotIn("git push\n", text.replace("git push --force", ""))

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

    def test_apply_readme_skips_markers_inside_a_code_fence(self) -> None:
        start = self.mod.DEFAULT_START
        end = self.mod.DEFAULT_END
        text = (
            "## How\n"
            "\n"
            "```markdown\n"
            f"{start}\n"
            f"{end}\n"
            "```\n"
            "\n"
            "## Contributors\n"
            f"{start}\n"
            "old\n"
            f"{end}\n"
        )
        out = self.mod.apply_readme(text, "new\n")
        self.assertIn("```markdown\n" + start + "\n" + end + "\n```", out)
        self.assertIn(f"{start}\nnew\n{end}", out)
        self.assertNotIn("old", out)

    def test_apply_readme_missing_markers_exits_with_example(self) -> None:
        start = self.mod.DEFAULT_START
        end = self.mod.DEFAULT_END
        for bad_text in ["# Just title\n", f"# Only start\n{start}\n", f"# Only end\n{end}\n"]:
            with self.subTest(bad_text=bad_text):
                with self.assertRaises(SystemExit) as ctx:
                    self.mod.apply_readme(bad_text, "new\n")
                self.assertNotEqual(ctx.exception.code, 0)
                msg = str(ctx.exception)
                self.assertIn(start, msg)
                self.assertIn(end, msg)

    def test_apply_readme_missing_markers_includes_custom_markers(self) -> None:
        custom_start = "<!-- custom-start -->"
        custom_end = "<!-- custom-end -->"
        with mock.patch.dict("os.environ", {"MARKER_START": custom_start, "MARKER_END": custom_end}):
            with self.assertRaises(SystemExit) as ctx:
                self.mod.apply_readme("# Just title\n", "new\n")
            self.assertNotEqual(ctx.exception.code, 0)
            msg = str(ctx.exception)
            self.assertIn(custom_start, msg)
            self.assertIn(custom_end, msg)

    def test_empty_list_is_a_first_invite(self) -> None:
        html = self.mod.render_html([])
        wall = self.mod.render_wall([])
        self.assertIn("Be the first to appear here.", html)
        self.assertIn("Be the first to appear here.", wall)
        self.assertNotIn("<table>", wall)
        self.assertIn("<svg", self.mod.render_svg([]))

    def test_exclude_drops_logins_after_bots(self) -> None:
        people = self.mod.merge_people(
            [{"login": "alice", "name": "Alice"}, {"login": "bob", "name": "Bob"}],
            [{"login": "cara", "name": "Cara", "type": "User"}],
            limit=48,
            exclude="Bob, ghost",
        )
        self.assertEqual(
            [person["login"] for person in people],
            ["alice", "cara"],
        )

    def test_sticker_keeps_short_label_and_full_name(self) -> None:
        svg = self.mod.render_sticker_svg(
            {"login": "alice", "name": "Alice Very Long Example"}
        )
        self.assertIn(self.mod._short_label("Alice Very Long Example"), svg)
        self.assertIn('aria-label="Alice Very Long Example"', svg)
        self.assertIn("<title>Alice Very Long Example</title>", svg)
        self.assertNotEqual(
            self.mod._short_label("Alice Very Long Example"),
            "Alice Very Long Example",
        )

    def test_merged_pr_coauthors_join_the_wall(self) -> None:
        extras = self.mod.merged_pr_people(
            [
                {
                    "merged_at": "2026-09-07T08:27:53Z",
                    "user": {"login": "HeaTTap", "type": "User"},
                    "body": (
                        "Thanks\n\n"
                        "Co-authored-by: Bob <123+bob@users.noreply.github.com>\n"
                        "Co-authored-by: dependabot[bot] "
                        "<bot@users.noreply.github.com>\n"
                    ),
                }
            ]
        )
        people = self.mod.merge_people(
            [{"login": "owner", "name": "Owner"}], extras, limit=48
        )
        self.assertEqual(
            [person["login"] for person in people],
            ["owner", "HeaTTap", "bob"],
        )

    def test_caption_auto_uses_model_and_omits_junk(self) -> None:
        people = [{"login": f"u{i}", "name": f"User {i}"} for i in range(12)]
        env = {
            "CAPTION": "auto",
            "MODEL_API_KEY": "sk-test",
            "MODEL": "gpt-4o-mini",
        }
        with mock.patch.dict("os.environ", env, clear=False):
            self.mod._post_json = lambda *_a, **_k: {  # type: ignore[method-assign]
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"caption": "Twelve people keep py-harness honest."}'
                            )
                        }
                    }
                ]
            }
            self.assertEqual(
                self.mod.ask_caption(people, "YauhenBichel/py-harness"),
                "Twelve people keep py-harness honest.",
            )
            self.mod._post_json = lambda *_a, **_k: {  # type: ignore[method-assign]
                "choices": [{"message": {"content": '{"caption": "nsfw wall"}'}}]
            }
            self.assertEqual(
                self.mod.ask_caption(people, "YauhenBichel/py-harness"), ""
            )
            self.mod._post_json = lambda *_a, **_k: {  # type: ignore[method-assign]
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"caption": "The contributors wall showcases '
                                'the efforts of 12 dedicated individuals."}'
                            )
                        }
                    }
                ]
            }
            self.assertEqual(
                self.mod.ask_caption(people, "YauhenBichel/py-harness"), ""
            )
        wall = self.mod.render_wall(
            [{"login": "alice", "name": "Alice"}],
            caption="Twelve people keep py-harness honest.",
        )
        self.assertIn("Twelve people keep py-harness honest.", wall)
        self.assertEqual(self.mod.ask_caption(people[:3]), "")
        self.assertFalse(
            self.mod.caption_is_specific(
                "The contributors wall showcases the efforts of 2 dedicated individuals.",
                people[:2],
                "YauhenBichel/readme-contributors",
            )
        )
        self.assertTrue(
            self.mod.caption_is_specific(
                "Yauhen Bichel and HeaTTap keep readme-contributors current.",
                [
                    {"login": "YauhenBichel", "name": "Yauhen Bichel"},
                    {"login": "HeaTTap", "name": "HeaTTap"},
                ],
                "YauhenBichel/readme-contributors",
            )
        )

    def test_caption_reuses_specific_line_when_roster_matches(self) -> None:
        people = [
            {"login": "YauhenBichel", "name": "Yauhen Bichel"},
            {"login": "HeaTTap", "name": "HeaTTap"},
        ]
        line = "Yauhen Bichel and HeaTTap keep readme-contributors current."
        wall = self.mod.render_wall(people, format="html", caption=line)
        text = f"{self.mod.DEFAULT_START}\n{wall}{self.mod.DEFAULT_END}\n"
        env = {
            "CAPTION": "auto",
            "MODEL_API_KEY": "sk-test",
            "MODEL": "gpt-4o-mini",
        }

        def boom(*_a, **_k):
            raise AssertionError("model should not be called")

        with mock.patch.dict("os.environ", env, clear=False):
            self.mod._post_json = boom  # type: ignore[method-assign]
            self.assertEqual(
                self.mod.resolve_caption(
                    people, "YauhenBichel/readme-contributors", text
                ),
                line,
            )
            stock = self.mod.render_wall(
                people,
                format="html",
                caption=(
                    "The contributors wall showcases the efforts of "
                    "2 dedicated individuals."
                ),
            )
            stock_text = f"{self.mod.DEFAULT_START}\n{stock}{self.mod.DEFAULT_END}\n"
            seen: list[dict] = []

            def fake(_url, _key, payload):
                seen.append(payload)
                return {
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    '{"caption": "Yauhen Bichel ships '
                                    'readme-contributors."}'
                                )
                            }
                        }
                    ]
                }

            self.mod._post_json = fake  # type: ignore[method-assign]
            self.assertEqual(
                self.mod.resolve_caption(
                    people, "YauhenBichel/readme-contributors", stock_text
                ),
                "Yauhen Bichel ships readme-contributors.",
            )
            self.assertEqual(seen[0]["temperature"], 0)
            extra = people + [{"login": "alice", "name": "Alice"}]
            self.assertEqual(
                self.mod.resolve_caption(
                    extra, "YauhenBichel/readme-contributors", text
                ),
                "Yauhen Bichel ships readme-contributors.",
            )
            self.assertEqual(len(seen), 2)

    def test_trigger_actor_is_added_when_api_lags(self) -> None:
        api = [{"login": "alice", "name": "Alice"}]
        extras = self.mod.trigger_people(actor="bob")
        people = self.mod.merge_people(api, extras, limit=48)
        self.assertEqual(
            people,
            [
                {"login": "alice", "name": "Alice"},
                {"login": "bob", "name": "bob"},
            ],
        )

    def test_trigger_bot_actor_is_ignored(self) -> None:
        api = [{"login": "alice", "name": "Alice"}]
        extras = self.mod.trigger_people(actor="github-actions[bot]")
        people = self.mod.merge_people(api, extras, limit=48)
        self.assertEqual(people, [{"login": "alice", "name": "Alice"}])

    def test_trigger_actor_already_listed_stays_one_row(self) -> None:
        api = [{"login": "alice", "name": "Alice"}]
        extras = self.mod.trigger_people(actor="alice")
        people = self.mod.merge_people(api, extras, limit=48)
        self.assertEqual(people, [{"login": "alice", "name": "Alice"}])

    def test_trigger_people_reads_pull_request_author(self) -> None:
        extras = self.mod.trigger_people(
            actor="owner",
            event={"pull_request": {"user": {"login": "HeaTTap", "type": "User"}}},
        )
        people = self.mod.merge_people(
            [{"login": "owner", "name": "Owner"}], extras, limit=48
        )
        self.assertEqual(
            [person["login"] for person in people],
            ["owner", "HeaTTap"],
        )

    def test_merged_pr_author_is_added_when_api_has_only_merger(self) -> None:
        api = [{"login": "owner", "name": "Owner"}]
        extras = self.mod.merged_pr_people(
            [
                {
                    "merged_at": "2026-09-07T08:27:53Z",
                    "user": {"login": "HeaTTap", "type": "User"},
                }
            ]
        )
        people = self.mod.merge_people(api, extras, limit=48)
        self.assertEqual(
            [person["login"] for person in people],
            ["owner", "HeaTTap"],
        )

    def test_merged_pr_bots_stay_off_the_wall(self) -> None:
        extras = self.mod.merged_pr_people(
            [
                {
                    "merged_at": "2026-09-01T00:00:00Z",
                    "user": {"login": "dependabot[bot]", "type": "Bot"},
                },
                {"user": {"login": "not-merged", "type": "User"}},
            ]
        )
        people = self.mod.merge_people(
            [{"login": "alice", "name": "Alice"}], extras, limit=48
        )
        self.assertEqual(people, [{"login": "alice", "name": "Alice"}])

    def test_list_people_adds_actor_and_merged_pr_without_live_api(self) -> None:
        def fake_get(url: str, _token: str) -> object:
            if "/contributors" in url:
                return [{"login": "alice", "type": "User"}]
            if url.endswith("/users/alice"):
                return {"name": "Alice", "type": "User"}
            if url.endswith("/users/bob"):
                return {"name": "Bob", "type": "User"}
            if url.endswith("/users/HeaTTap"):
                return {"name": "HeaTTap", "type": "User"}
            if url.endswith("/users/cara"):
                return {"name": "Cara", "type": "User"}
            if "/pulls?" in url:
                return [
                    {
                        "merged_at": "2026-09-07T08:27:53Z",
                        "user": {"login": "HeaTTap", "type": "User"},
                        "body": "Co-authored-by: Cara <cara@users.noreply.github.com>",
                    }
                ]
            raise AssertionError(url)

        self.mod._get = fake_get  # type: ignore[method-assign]
        env = {"GITHUB_ACTOR": "bob", "GITHUB_EVENT_PATH": ""}
        with mock.patch.dict("os.environ", env, clear=False):
            people = self.mod.list_people("owner/name", "token", limit=48)
        self.assertEqual(
            people,
            [
                {"login": "alice", "name": "Alice"},
                {"login": "bob", "name": "Bob"},
                {"login": "HeaTTap", "name": "HeaTTap"},
                {"login": "cara", "name": "Cara"},
            ],
        )

    def test_contributors_repo_wins_over_github_repository(self) -> None:
        """Actions ignores GITHUB_REPOSITORY in a composite env block."""
        seen: list[str] = []

        def people(repo: str, _token: str, limit: int = 48, exclude: str = ""):
            seen.append(repo)
            return []

        self.mod.list_people = people  # type: ignore[method-assign]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            start = self.mod.DEFAULT_START
            end = self.mod.DEFAULT_END
            readme.write_text(f"{start}\n{end}\n", encoding="utf-8")
            env = {
                "GITHUB_WORKSPACE": str(root),
                "GITHUB_REPOSITORY": "this/repo",
                "CONTRIBUTORS_REPO": "YauhenBichel/py-harness",
                "FORMAT": "html",
            }
            old = {key: __import__("os").environ.get(key) for key in env}
            try:
                for key, value in env.items():
                    __import__("os").environ[key] = value
                with mock.patch("sys.stdout", new=StringIO()):
                    self.mod.main()
            finally:
                for key, value in old.items():
                    if value is None:
                        __import__("os").environ.pop(key, None)
                    else:
                        __import__("os").environ[key] = value
        self.assertEqual(seen, ["YauhenBichel/py-harness"])

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

            def people(_repo: str, _token: str, limit: int = 48, exclude: str = ""):
                return [{"login": "alice", "name": "Alice"}]

            self.mod.list_people = people  # type: ignore[method-assign]
            self.mod.fetch_avatars = lambda *_a, **_k: {}  # type: ignore[method-assign]
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
