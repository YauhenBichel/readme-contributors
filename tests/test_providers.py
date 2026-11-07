"""Caption examples for providers other than OpenAI (issues #58-#61)."""

from __future__ import annotations

import importlib.util
import json
import os
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FILL = ROOT / "fill.py"

PROVIDERS = {
    "anthropic": ("ANTHROPIC_API_KEY", "https://api.anthropic.com/v1"),
    "gemini": ("GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai"),
    "groq": ("GROQ_API_KEY", "https://api.groq.com/openai/v1"),
    "huggingface": ("HF_TOKEN", "https://router.huggingface.co/v1"),
}


def _load():
    spec = importlib.util.spec_from_file_location("readme_contributors_fill", FILL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExampleTest(unittest.TestCase):
    def test_each_example_uses_its_own_provider(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for name, (secret, base) in PROVIDERS.items():
            path = f"examples/contributors-{name}.yml"
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(name):
                self.assertIn(f"model-api-key: ${{{{ secrets.{secret} }}}}", text)
                self.assertIn(f"model-base-url: {base}", text)
                self.assertIn("caption: auto", text)
                self.assertNotIn("OPENAI_API_KEY", text)
                self.assertIn(path, readme)


class RequestTest(unittest.TestCase):
    def _payload(self, base: str) -> dict:
        mod = _load()
        sent: list[dict] = []
        reply = {"choices": [{"message": {"content": json.dumps({"caption": "Ada built demo."})}}]}

        def post(url: str, key: str, payload: dict) -> object:
            sent.append({"url": url, **payload})
            return reply

        env = {"CAPTION": "auto", "MODEL": "m", "MODEL_API_KEY": "k", "MODEL_BASE_URL": base}
        with mock.patch.dict(os.environ, env, clear=False), mock.patch.object(mod, "_post_json", side_effect=post), mock.patch("sys.stderr"):
            mod.ask_caption([{"login": "ada", "name": "Ada"}], "owner/demo")
        self.assertEqual(len(sent), 1)
        return sent[0]

    def test_anthropic_gets_no_temperature(self) -> None:
        payload = self._payload("https://api.anthropic.com/v1")
        self.assertEqual(payload["url"], "https://api.anthropic.com/v1/chat/completions")
        self.assertNotIn("temperature", payload)
        self.assertEqual(payload["max_tokens"], 80)

    def test_other_providers_keep_temperature_zero(self) -> None:
        for name, (_, base) in PROVIDERS.items():
            if name == "anthropic":
                continue
            with self.subTest(name):
                payload = self._payload(base)
                self.assertEqual(payload["url"], f"{base}/chat/completions")
                self.assertEqual(payload["temperature"], 0)


if __name__ == "__main__":
    unittest.main()
