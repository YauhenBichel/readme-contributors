"""A merged pull request's body stays editable by its author, so the wall must
not trust it too far. Found by a security review on 11 September 2026."""

from __future__ import annotations

import importlib.util
import io
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError

FILL = Path(__file__).resolve().parents[1] / "fill.py"


def _load():
    spec = importlib.util.spec_from_file_location("readme_contributors_fill", FILL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CoauthorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = _load()

    def test_a_bare_login_is_not_a_coauthor(self) -> None:
        self.assertEqual(self.mod.parse_coauthor_logins("Co-authored-by: torvalds\nCo-authored-by: @gaearon"), [])

    def test_coauthors_per_pull_request_are_capped(self) -> None:
        body = "\n".join(f"Co-authored-by: P{i} <{i}+p{i}@users.noreply.github.com>" for i in range(40))
        people = self.mod.merged_pr_people([{"merged_at": "2026-09-07T08:27:53Z", "body": body}])
        self.assertEqual(len(people), self.mod.MAX_COAUTHORS)

    def test_an_unknown_login_is_skipped_not_fatal(self) -> None:
        missing = HTTPError("https://api.github.com/users/no-such-user", 404, "Not Found", {}, io.BytesIO(b""))
        with mock.patch.object(self.mod, "_get", side_effect=missing), mock.patch("sys.stderr", new=io.StringIO()):
            self.assertIsNone(self.mod._person_from_login("no-such-user", "token"))

    def test_other_api_errors_still_fail_the_run(self) -> None:
        # A rate limit must not quietly shrink the wall.
        limited = HTTPError("https://api.github.com/users/bob", 403, "rate limited", {}, io.BytesIO(b""))
        with mock.patch.object(self.mod, "_get", side_effect=limited):
            with self.assertRaises(HTTPError):
                self.mod._person_from_login("bob", "token")


class TokenTest(unittest.TestCase):
    def test_the_token_goes_only_to_the_api(self) -> None:
        mod = _load()
        sent: list[tuple[str, str | None]] = []

        class Response(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        def fake_urlopen(req, timeout=0):
            sent.append((req.full_url, req.get_header("Authorization")))
            return Response(b"x")

        with mock.patch.object(mod, "urlopen", side_effect=fake_urlopen):
            mod._bytes(f"{mod.AVATARS}/bob?s=96", "secret-token")
            mod._bytes(f"{mod.API}/repos/o/r/contents/x", "secret-token")
        self.assertIsNone(sent[0][1], "the avatar host received the token")
        self.assertEqual(sent[1][1], "Bearer secret-token")


if __name__ == "__main__":
    unittest.main()
