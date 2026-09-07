#!/usr/bin/env python3
"""Fill a README contributors wall from the GitHub API.

Bots are omitted. The README wall is one clickable polaroid sticker
per person (GitHub cannot click inside a single SVG image). The SVG
file is still written for Pages. Layouts and themes change the
drawing; they do not change who is listed.
"""

from __future__ import annotations

import base64
import html
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Mapping
from urllib.error import URLError
from urllib.request import Request, urlopen

API = "https://api.github.com"
AVATARS = "https://avatars.githubusercontent.com"
DEFAULT_START = "<!-- readme: contributors,bots/- -start -->"
DEFAULT_END = "<!-- readme: contributors,bots/- -end -->"
EMPTY_WALL = "Be the first to appear here."
GITHUB_MODELS_URL = "https://models.github.ai/inference"
_COAUTHOR_LINE = re.compile(r"(?im)^[ \t]*co-authored-by:[ \t]+(.+)$")
_GITHUB_NOREPLY = re.compile(
    r"(?:(?P<id>\d+)\+)?(?P<login>[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?)"
    r"@users\.noreply\.github\.com$",
    re.I,
)
_LOGIN_TOKEN = re.compile(
    r"^@?(?P<login>[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?)\b"
)
_CAPTION_EM = re.compile(r"<em>(.*?)</em>", re.I | re.S)
_WALL_HREF = re.compile(r'href="https://github.com/([^"#?]+)"', re.I)
_UNSAFE = (
    "nsfw",
    "porn",
    "sex",
    "nude",
    "xxx",
    "kill yourself",
    "kys",
    "suicide",
)
# 1x1 PNG used only when a test injects a known image.
TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)
LAYOUTS = (
    "facepile",
    "stickers",
    "grid",
    "tiles",
    "list",
    "compact",
    "wave",
    "orbit",
    "honeycomb",
    "ribbon",
    "constellation",
    "banner",
)
_STICKER_TILT = (-9, 7, -5, 11, -8, 4)
_STICKER_SCALE = (1.22, 0.92, 1.0, 1.12, 0.88, 1.06)
THEMES = {
    "auto": {
        "ring": "#ffffff",
        "ring_dark": "#0d1117",
        "label": "#24292f",
        "label_dark": "#e6edf3",
        "bg": "",
        "card": "",
        "muted": "#57606a",
    },
    "github": {
        "ring": "#ffffff",
        "ring_dark": "#0d1117",
        "label": "#1f2328",
        "label_dark": "#e6edf3",
        "bg": "",
        "card": "",
        "muted": "#656d76",
    },
    "midnight": {
        "ring": "#30363d",
        "label": "#e6edf3",
        "bg": "#0d1117",
        "card": "#161b22",
        "muted": "#8b949e",
    },
    "sunrise": {
        "ring": "#fff7ed",
        "label": "#7c2d12",
        "bg": "#fff7ed",
        "card": "#ffedd5",
        "muted": "#c2410c",
    },
    "forest": {
        "ring": "#ecfdf3",
        "label": "#14532d",
        "bg": "#f0fdf4",
        "card": "#dcfce7",
        "muted": "#15803d",
    },
    "ocean": {
        "ring": "#e0f2fe",
        "label": "#0c4a6e",
        "bg": "#f0f9ff",
        "card": "#e0f2fe",
        "muted": "#0369a1",
    },
    "mono": {
        "ring": "#f6f8fa",
        "label": "#1f2328",
        "bg": "#f6f8fa",
        "card": "#eaeef2",
        "muted": "#59636e",
    },
}


def _root() -> Path:
    workspace = os.environ.get("GITHUB_WORKSPACE", "").strip()
    return Path(workspace) if workspace else Path.cwd()


def _start() -> str:
    return os.environ.get("MARKER_START", DEFAULT_START)


def _end() -> str:
    return os.environ.get("MARKER_END", DEFAULT_END)


def _xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _get(url: str, token: str) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "readme-contributors-action",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, headers=headers)
    with urlopen(req, timeout=30) as resp:
        return json.load(resp)


def _bytes(url: str, token: str) -> bytes:
    headers = {"User-Agent": "readme-contributors-action"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, headers=headers)
    with urlopen(req, timeout=20) as resp:
        return resp.read()


def is_human_login(login: str, kind: str = "") -> bool:
    if not (login or "").strip():
        return False
    if (kind or "").lower() == "bot":
        return False
    return not login.lower().endswith("[bot]")


def parse_exclude(raw: str) -> frozenset[str]:
    return frozenset(
        part.strip().lower() for part in (raw or "").split(",") if part.strip()
    )


def is_excluded(login: str, blocked: frozenset[str]) -> bool:
    return (login or "").strip().lower() in blocked


def parse_coauthor_logins(*texts: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    blob = "\n".join(text or "" for text in texts)
    for match in _COAUTHOR_LINE.finditer(blob):
        login = _coauthor_login(match.group(1))
        key = login.lower()
        if not login or key in seen or not is_human_login(login):
            continue
        seen.add(key)
        found.append(login)
    return found


def _coauthor_login(rest: str) -> str:
    raw = (rest or "").strip()
    name_part = raw.split("<", 1)[0].strip()
    if not is_human_login(name_part):
        return ""
    email_match = re.search(r"<([^>]+)>", raw)
    if email_match:
        email = email_match.group(1).strip()
        noreply = _GITHUB_NOREPLY.search(email)
        if noreply:
            return noreply.group("login")
        return ""
    token = _LOGIN_TOKEN.match(raw)
    return token.group("login") if token else ""


def merge_people(
    people: list[dict[str, str]],
    extras: list[dict[str, str]],
    limit: int,
    exclude: str = "",
) -> list[dict[str, str]]:
    """Append unique humans from extras without growing past limit."""
    blocked = parse_exclude(exclude)
    seen = {person["login"].lower() for person in people}
    out = [person for person in people if not is_excluded(person["login"], blocked)]
    for extra in extras:
        if len(out) >= limit:
            break
        login = str(extra.get("login") or "").strip()
        kind = str(extra.get("type") or "")
        if (
            not is_human_login(login, kind)
            or login.lower() in seen
            or is_excluded(login, blocked)
        ):
            continue
        seen.add(login.lower())
        name = str(extra.get("name") or "").strip() or login
        out.append({"login": login, "name": name})
    return out


def trigger_people(
    actor: str = "",
    event: Mapping[str, object] | None = None,
) -> list[dict[str, str]]:
    """Authors of the commit or pull request that triggered this job."""
    extras: list[dict[str, str]] = []
    if actor.strip():
        extras.append({"login": actor.strip(), "name": actor.strip()})
    if not isinstance(event, Mapping):
        return extras

    def _add_user(user: object) -> None:
        if not isinstance(user, Mapping):
            return
        login = str(user.get("login") or user.get("username") or "").strip()
        if not login:
            return
        extras.append(
            {
                "login": login,
                "name": str(user.get("name") or login),
                "type": str(user.get("type") or ""),
            }
        )

    pull = event.get("pull_request")
    if isinstance(pull, Mapping):
        _add_user(pull.get("user"))

    head = event.get("head_commit")
    if isinstance(head, Mapping):
        _add_user(head.get("author"))

    commits = event.get("commits")
    if isinstance(commits, list):
        for row in commits:
            if isinstance(row, Mapping):
                _add_user(row.get("author"))
    return extras


def load_event(path: str = "") -> dict[str, object]:
    raw = (path or os.environ.get("GITHUB_EVENT_PATH", "")).strip()
    if not raw:
        return {}
    file = Path(raw)
    if not file.is_file():
        return {}
    data = json.loads(file.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def merged_pr_people(rows: object) -> list[dict[str, str]]:
    extras: list[dict[str, str]] = []
    if not isinstance(rows, list):
        return extras
    for row in rows:
        if not isinstance(row, dict) or not row.get("merged_at"):
            continue
        user = row.get("user")
        if isinstance(user, dict):
            login = str(user.get("login") or "").strip()
            if login:
                extras.append(
                    {
                        "login": login,
                        "name": str(user.get("name") or login),
                        "type": str(user.get("type") or ""),
                    }
                )
        for login in parse_coauthor_logins(str(row.get("body") or "")):
            extras.append({"login": login, "name": login, "type": "User"})
    return extras


def _person_from_login(login: str, token: str, kind: str = "") -> dict[str, str] | None:
    if not is_human_login(login, kind):
        return None
    profile = _get(f"{API}/users/{login}", token)
    name = login
    if isinstance(profile, dict):
        if str(profile.get("type") or "").lower() == "bot":
            return None
        if profile.get("name"):
            name = str(profile["name"])
    return {"login": login, "name": name}


def _append_resolved(
    people: list[dict[str, str]],
    extras: list[dict[str, str]],
    token: str,
    limit: int,
    exclude: str = "",
) -> list[dict[str, str]]:
    blocked = parse_exclude(exclude)
    pending: list[dict[str, str]] = []
    seen = {person["login"].lower() for person in people}
    for extra in extras:
        if len(people) + len(pending) >= limit:
            break
        login = str(extra.get("login") or "").strip()
        kind = str(extra.get("type") or "")
        if (
            not is_human_login(login, kind)
            or login.lower() in seen
            or is_excluded(login, blocked)
        ):
            continue
        person = _person_from_login(login, token, kind)
        if person is None:
            continue
        seen.add(login.lower())
        pending.append(person)
    return people + pending


def list_merged_pr_authors(
    repo: str, token: str, limit: int
) -> list[dict[str, str]]:
    extras: list[dict[str, str]] = []
    seen: set[str] = set()
    page = 1
    while len(seen) < limit:
        rows = _get(
            f"{API}/repos/{repo}/pulls?state=closed&per_page=100&page={page}",
            token,
        )
        batch = merged_pr_people(rows)
        extras.extend(batch)
        for extra in batch:
            login = str(extra.get("login") or "").strip().lower()
            if login:
                seen.add(login)
        if not isinstance(rows, list) or len(rows) < 100:
            break
        page += 1
    return extras


def list_people(
    repo: str, token: str, limit: int = 100, exclude: str = ""
) -> list[dict[str, str]]:
    blocked = parse_exclude(exclude)
    people: list[dict[str, str]] = []
    page = 1
    while len(people) < limit:
        rows = _get(
            f"{API}/repos/{repo}/contributors?per_page=100&anon=false&page={page}",
            token,
        )
        if not isinstance(rows, list) or not rows:
            break
        for row in rows:
            if len(people) >= limit:
                break
            if not isinstance(row, dict):
                continue
            login = str(row.get("login") or "")
            kind = str(row.get("type") or "")
            if is_excluded(login, blocked):
                continue
            person = _person_from_login(login, token, kind)
            if person is None:
                continue
            people.append(person)
        if len(rows) < 100:
            break
        page += 1
    extras = trigger_people(
        os.environ.get("GITHUB_ACTOR", ""),
        load_event(),
    )
    extras.extend(list_merged_pr_authors(repo, token, limit))
    return _append_resolved(people, extras, token, limit, exclude)


def fetch_avatars(
    people: list[dict[str, str]],
    token: str,
    size: int,
) -> dict[str, bytes]:
    found: dict[str, bytes] = {}
    pixel = max(size * 2, 96)
    for person in people:
        login = person["login"]
        try:
            found[login] = _bytes(f"{AVATARS}/{login}?s={pixel}", token)
        except (URLError, TimeoutError, OSError) as exc:
            print(f"avatar skipped for {login}: {exc}", file=sys.stderr)
    return found


def _initials(name: str) -> str:
    parts = [part for part in name.replace(".", " ").split() if part]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return f"{parts[0][0]}{parts[-1][0]}".upper()


def _hue(login: str) -> int:
    return sum(ord(char) for char in login) % 360


def _mime(payload: bytes) -> str:
    if payload.startswith(b"\x89PNG"):
        return "image/png"
    if payload.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if payload.startswith(b"RIFF") and b"WEBP" in payload[:16]:
        return "image/webp"
    if payload.startswith(b"GIF8"):
        return "image/gif"
    return "application/octet-stream"


def _data_uri(payload: bytes) -> str:
    encoded = base64.b64encode(payload).decode("ascii")
    return f"data:{_mime(payload)};base64,{encoded}"


def parse_layout(raw: str) -> str:
    name = (raw or "auto").strip().lower() or "auto"
    if name == "auto":
        return "auto"
    if name not in LAYOUTS:
        allowed = "auto, " + ", ".join(LAYOUTS)
        raise SystemExit(f"layout must be one of: {allowed}")
    return name


def fit_layout(layout: str, count: int) -> str:
    """Pages SVG. auto picks a layout that still shows every face."""
    chosen = parse_layout(layout)
    if chosen != "auto":
        return chosen
    if count <= 8:
        return "facepile"
    if count <= 24:
        return "grid"
    return "compact"


def fit_readme_size(count: int, size: int) -> int:
    """README polaroids shrink so a long list still wraps on GitHub."""
    size = max(32, size)
    if count <= 20:
        return size
    if count <= 50:
        return min(size, 48)
    return min(size, 36)


def parse_theme(raw: str) -> str:
    name = (raw or "auto").strip().lower() or "auto"
    if name not in THEMES:
        allowed = ", ".join(THEMES)
        raise SystemExit(f"theme must be one of: {allowed}")
    return name


def _font() -> str:
    return (
        "-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, "
        "sans-serif"
    )


def _theme_css(theme: Mapping[str, str]) -> list[str]:
    lines = [
        "<style>",
        f".ring {{ fill: none; stroke: {theme['ring']}; stroke-width: 4; }}",
        f".label {{ fill: {theme['label']}; font-family: {_font()}; "
        "font-weight: 600; }",
        f".muted {{ fill: {theme['muted']}; font-family: {_font()}; }}",
        f".link {{ fill: none; stroke: {theme['muted']}; stroke-width: 1.5; "
        "stroke-opacity: 0.55; pointer-events: none; }",
    ]
    if theme.get("ring_dark"):
        lines.extend(
            [
                "@media (prefers-color-scheme: dark) {",
                f"  .ring {{ stroke: {theme['ring_dark']}; }}",
                f"  .label {{ fill: {theme.get('label_dark', theme['label'])}; }}",
                "}",
            ]
        )
    lines.append("</style>")
    return lines


def _placements(
    layout: str,
    count: int,
    size: int,
    columns: int,
    framed: bool,
) -> tuple[int, int, list[tuple[int, float, float, int]]]:
    """Return canvas size and (index, x, y, face_size) for each person."""
    columns = max(1, columns)
    size = max(32, size)
    spots: list[tuple[int, float, float, int]] = []
    if count <= 0:
        return 1, 1, spots

    if layout == "facepile":
        pad = 10 if framed else 4
        step = int(size * 0.64)
        row_gap = 14
        rows = (count + columns - 1) // columns
        widest = min(columns, count)
        width = pad * 2 + size + step * max(0, widest - 1)
        height = pad * 2 + size * rows + row_gap * max(0, rows - 1)
        for index in range(count):
            column = index % columns
            row = index // columns
            spots.append(
                (index, float(pad + column * step), float(pad + row * (size + row_gap)), size)
            )
        return width, height, spots

    if layout == "list":
        pad = 14 if framed else 12
        row_gap = 10
        name_w = 168
        width = pad * 2 + size + 14 + name_w
        height = pad * 2 + size * count + row_gap * max(0, count - 1)
        for index in range(count):
            spots.append((index, float(pad), float(pad + index * (size + row_gap)), size))
        return width, height, spots

    if layout == "wave":
        pad = 14 if framed else 8
        amp = int(size * 0.42)
        step = int(size * 0.82)
        cols = min(columns, count)
        rows = (count + cols - 1) // cols
        width = pad * 2 + step * max(0, cols - 1) + size
        height = pad * 2 + rows * (size + 2 * amp) - amp
        for index in range(count):
            column = index % cols
            row = index // cols
            wave = amp + int(amp * math.sin(column * 0.95 + row))
            spots.append(
                (
                    index,
                    float(pad + column * step),
                    float(pad + row * (size + 2 * amp) + wave),
                    size,
                )
            )
        return width, height, spots

    if layout == "orbit":
        pad = 16 if framed else 12
        if count == 1:
            width = pad * 2 + size
            height = pad * 2 + size
            spots.append((0, float(pad), float(pad), size))
            return width, height, spots
        ring = size * (0.95 + 0.08 * min(count, 10))
        hero = int(size * 1.12)
        canvas = int(2 * (ring + size / 2) + pad * 2)
        cx = canvas / 2
        cy = canvas / 2
        spots.append((0, cx - hero / 2, cy - hero / 2, hero))
        around = count - 1
        for index in range(1, count):
            angle = -math.pi / 2 + 2 * math.pi * (index - 1) / around
            spots.append(
                (
                    index,
                    cx + ring * math.cos(angle) - size / 2,
                    cy + ring * math.sin(angle) - size / 2,
                    size,
                )
            )
        return canvas, canvas, spots

    if layout == "honeycomb":
        pad = 14 if framed else 8
        pitch_x = size + 8
        pitch_y = int(size * 0.86) + 6
        rows = (count + columns - 1) // columns
        width = pad * 2 + columns * pitch_x + pitch_x // 2
        height = pad * 2 + rows * pitch_y + size - pitch_y
        for index in range(count):
            column = index % columns
            row = index // columns
            ox = (pitch_x / 2) if row % 2 else 0
            spots.append(
                (
                    index,
                    float(pad + ox + column * pitch_x),
                    float(pad + row * pitch_y),
                    size,
                )
            )
        return width, height, spots

    if layout == "ribbon":
        pad = 14 if framed else 8
        step_x = int(size * 0.72)
        step_y = int(size * 0.36)
        width = pad * 2 + step_x * max(0, count - 1) + size
        height = pad * 2 + size + step_y
        for index in range(count):
            spots.append(
                (
                    index,
                    float(pad + index * step_x),
                    float(pad + (step_y if index % 2 else 0)),
                    size,
                )
            )
        return width, height, spots

    if layout == "constellation":
        pad = 16 if framed else 10
        step = int(size * 1.15)
        cols = min(columns, count)
        rows = (count + cols - 1) // cols
        width = pad * 2 + step * max(0, cols - 1) + size
        height = pad * 2 + (size + 28) * max(0, rows - 1) + size
        for index in range(count):
            column = index % cols
            row = index // cols
            jitter = 10 if (index + row) % 2 else 0
            spots.append(
                (
                    index,
                    float(pad + column * step + (8 if row % 2 else 0)),
                    float(pad + row * (size + 28) + jitter),
                    size,
                )
            )
        return width, height, spots

    if layout == "banner":
        pad = 14 if framed else 10
        hero = int(size * 1.55)
        side_cols = min(3, max(1, count - 1))
        rest = max(0, count - 1)
        side_rows = (rest + side_cols - 1) // side_cols if rest else 0
        gap = 12
        width = pad * 2 + hero + (gap + (size + 10) * side_cols if rest else 0)
        height = pad * 2 + max(hero, side_rows * (size + 10) - 10 if rest else hero)
        spots.append((0, float(pad), float(pad), hero))
        for index in range(1, count):
            slot = index - 1
            column = slot % side_cols
            row = slot // side_cols
            spots.append(
                (
                    index,
                    float(pad + hero + gap + column * (size + 10)),
                    float(pad + row * (size + 10)),
                    size,
                )
            )
        return width, height, spots

    if layout == "stickers":
        pad = 28 if framed else 22
        step = int(size * 1.24)
        row_gap = int(size * 0.46)
        rows = (count + columns - 1) // columns
        widest = min(columns, count)
        width = pad * 2 + step * max(0, widest - 1) + size
        height = pad * 2 + (size + row_gap) * max(0, rows - 1) + size
        for index in range(count):
            column = index % columns
            row = index // columns
            spots.append(
                (
                    index,
                    float(pad + column * step),
                    float(pad + row * (size + row_gap)),
                    size,
                )
            )
        return width, height, spots

    if layout == "compact":
        pad = 10 if framed else 6
        step = size + 6
        row_gap = 6
    elif layout == "tiles":
        pad = 14 if framed else 10
        step = size + 14
        row_gap = 14
    else:
        pad = 12 if framed else 8
        step = size + 12
        row_gap = 12
    rows = (count + columns - 1) // columns
    widest = min(columns, count)
    width = pad * 2 + step * max(0, widest - 1) + size
    height = pad * 2 + (size + row_gap) * max(0, rows - 1) + size
    for index in range(count):
        column = index % columns
        row = index // columns
        spots.append(
            (index, float(pad + column * step), float(pad + row * (size + row_gap)), size)
        )
    return width, height, spots


def _hex_points(cx: float, cy: float, radius: float) -> str:
    parts = []
    for step in range(6):
        angle = math.radians(30 + 60 * step)
        parts.append(f"{cx + radius * math.cos(angle):.1f},{cy + radius * math.sin(angle):.1f}")
    return " ".join(parts)


def _paint_face(
    defs: list[str],
    body: list[str],
    *,
    index: int,
    person: Mapping[str, str],
    pictures: Mapping[str, bytes],
    x: float,
    y: float,
    size: int,
    shape: str,
) -> None:
    login = person["login"]
    name = person["name"]
    cx = x + size / 2
    cy = y + size / 2
    radius = size / 2
    clip = f"c{index}"
    if shape == "tile":
        radius_x = size * 0.2
        defs.append(
            f'<clipPath id="{clip}">'
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{size}" height="{size}" '
            f'rx="{radius_x:.1f}"/>'
            "</clipPath>"
        )
    elif shape == "hex":
        defs.append(
            f'<clipPath id="{clip}">'
            f'<polygon points="{_hex_points(cx, cy, radius)}"/>'
            "</clipPath>"
        )
    else:
        defs.append(
            f'<clipPath id="{clip}">'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}"/>'
            "</clipPath>"
        )
    payload = pictures.get(login)
    if payload:
        href = _data_uri(payload)
        body.append(
            f'<image href="{href}" x="{x:.1f}" y="{y:.1f}" '
            f'width="{size}" height="{size}" '
            f'clip-path="url(#{clip})" />'
        )
    else:
        hue = _hue(login)
        initials = _xml(_initials(name))
        if shape == "tile":
            body.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{size}" height="{size}" '
                f'rx="{size * 0.2:.1f}" fill="hsl({hue}, 42%, 46%)"/>'
            )
        elif shape == "hex":
            body.append(
                f'<polygon points="{_hex_points(cx, cy, radius)}" '
                f'fill="hsl({hue}, 42%, 46%)"/>'
            )
        else:
            body.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" '
                f'fill="hsl({hue}, 42%, 46%)"/>'
            )
        body.append(
            f'<text x="{cx:.1f}" y="{cy + size * 0.12:.1f}" '
            f'text-anchor="middle" fill="#ffffff" '
            f'font-size="{size * 0.34:.0f}" '
            f'font-family="{_font()}" '
            f'font-weight="600">{initials}</text>'
        )
    if shape == "tile":
        body.append(
            f'<rect class="ring" x="{x:.1f}" y="{y:.1f}" width="{size}" '
            f'height="{size}" rx="{size * 0.2:.1f}"/>'
        )
    elif shape == "hex":
        body.append(
            f'<polygon class="ring" points="{_hex_points(cx, cy, radius)}"/>'
        )
    else:
        body.append(
            f'<circle class="ring" cx="{cx:.1f}" cy="{cy:.1f}" '
            f'r="{radius:.1f}"/>'
        )


def render_svg(
    people: list[dict[str, str]],
    avatars: Mapping[str, bytes] | None = None,
    *,
    size: int = 72,
    columns: int = 8,
    layout: str = "facepile",
    theme: str = "auto",
) -> str:
    """Draw the wall. Each face is a link to that person's GitHub profile."""
    layout = fit_layout(layout, len(people))
    theme_name = parse_theme(theme)
    palette = THEMES[theme_name]
    if not people:
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1">'
            "</svg>\n"
        )
    pictures = avatars or {}
    framed = bool(palette.get("bg"))
    width, height, spots = _placements(
        layout, len(people), size, columns, framed
    )
    names = ", ".join(person["name"] for person in people)
    defs: list[str] = _theme_css(palette)
    if layout == "stickers":
        defs.extend(
            [
                '<filter id="lift" x="-20%" y="-20%" width="140%" height="140%">'
                '<feDropShadow dx="0" dy="3" stdDeviation="3" flood-opacity="0.22"/>'
                "</filter>",
                "<style>.ring { stroke-width: 7; }</style>",
            ]
        )
    body: list[str] = []
    if palette.get("bg"):
        body.append(
            f'<rect width="{width}" height="{height}" rx="16" '
            f'fill="{palette["bg"]}"/>'
        )
    if layout == "constellation" and len(spots) > 1:
        for left, right in zip(spots, spots[1:]):
            _ia, xa, ya, sa = left
            _ib, xb, yb, sb = right
            body.append(
                f'<line class="link" x1="{xa + sa / 2:.1f}" y1="{ya + sa / 2:.1f}" '
                f'x2="{xb + sb / 2:.1f}" y2="{yb + sb / 2:.1f}"/>'
            )
    if layout == "orbit" and len(people) > 1:
        _i0, x0, y0, s0 = spots[0]
        body.append(
            f'<circle class="link" cx="{x0 + s0 / 2:.1f}" '
            f'cy="{y0 + s0 / 2:.1f}" r="{s0 * 0.95 + size * 0.55:.1f}"/>'
        )
    shape = "tile" if layout == "tiles" else "hex" if layout == "honeycomb" else "circle"
    if layout == "facepile":
        draw = list(reversed(spots))
    elif layout == "orbit":
        draw = spots[1:] + spots[:1]
    else:
        draw = spots
    by_index = {index: person for index, person in enumerate(people)}
    for index, x, y, face in draw:
        person = by_index[index]
        if layout == "list" and palette.get("card"):
            body.append(
                f'<rect x="{x - 4:.1f}" y="{y - 4:.1f}" '
                f'width="{width - x * 2 + 8}" height="{face + 8}" '
                f'rx="12" fill="{palette["card"]}"/>'
            )
        face_bits: list[str] = []
        _paint_face(
            defs,
            face_bits,
            index=index,
            person=person,
            pictures=pictures,
            x=x,
            y=y,
            size=face,
            shape=shape,
        )
        if layout == "list":
            login = _xml(person["login"])
            label = _xml(person["name"])
            face_bits.append(
                f'<text class="label" x="{x + face + 14:.1f}" '
                f'y="{y + face * 0.42:.1f}" font-size="15">{label}</text>'
            )
            face_bits.append(
                f'<text class="muted" x="{x + face + 14:.1f}" '
                f'y="{y + face * 0.72:.1f}" font-size="12">@{login}</text>'
            )
        href = f"https://github.com/{_xml(person['login'])}"
        if layout == "stickers":
            hue = _hue(person["login"])
            face_bits.append(
                f'<circle cx="{x + face / 2:.1f}" cy="{y + face / 2:.1f}" '
                f'r="{face / 2:.1f}" fill="none" '
                f'stroke="hsl({hue}, 78%, 58%)" stroke-width="6"/>'
            )
            cx = x + face / 2
            cy = y + face / 2
            tilt = _STICKER_TILT[index % len(_STICKER_TILT)]
            body.append(
                f'<a href="{href}" target="_top">'
                f'<g transform="rotate({tilt} {cx:.1f} {cy:.1f})" '
                f'filter="url(#lift)">'
            )
            body.extend(face_bits)
            body.append("</g></a>")
        else:
            body.append(f'<a href="{href}" target="_top">')
            body.extend(face_bits)
            body.append("</a>")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" role="img" aria-label="{_xml(names)}">\n'
        f"<title>{_xml(names)}</title>\n"
        "<defs>\n"
        + "\n".join(defs)
        + "\n</defs>\n"
        + "\n".join(body)
        + "\n</svg>\n"
    )


def _sticker_size(size: int, index: int) -> int:
    return max(40, int(size * _STICKER_SCALE[index % len(_STICKER_SCALE)]))


def _face_file(login: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in login)
    return f"{safe or 'face'}.svg"


def _short_label(name: str, limit: int = 13) -> str:
    text = name.strip() or "?"
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def sticker_canvas(size: int) -> tuple[int, int]:
    """Pixel size of one polaroid SVG, including the tilt gutter."""
    size = max(32, size)
    inset = max(7, int(size * 0.11))
    band = max(20, int(size * 0.34))
    margin = max(10, int(size * 0.2))
    return size + inset * 2 + margin * 2, size + inset + band + margin * 2


def render_sticker_svg(
    person: Mapping[str, str],
    payload: bytes | None = None,
    *,
    size: int = 72,
    tilt: int = 0,
) -> str:
    """One tilted polaroid. Used as a README <img> so the face stays a link."""
    size = max(32, size)
    login = person["login"]
    name = person["name"]
    hue = _hue(login)
    inset = max(7, int(size * 0.11))
    band = max(20, int(size * 0.34))
    card_w = size + inset * 2
    card_h = size + inset + band
    margin = max(10, int(size * 0.2))
    width = card_w + margin * 2
    height = card_h + margin * 2
    ox = float(margin)
    oy = float(margin)
    fx = ox + inset + size / 2
    fy = oy + inset + size / 2
    radius = size / 2
    cx = width / 2
    cy = height / 2
    ring = max(5, int(size * 0.08))
    label = _xml(_short_label(name))
    defs = [
        '<filter id="lift" x="-25%" y="-25%" width="150%" height="150%">'
        '<feDropShadow dx="0" dy="2.5" stdDeviation="2.2" '
        'flood-color="#111827" flood-opacity="0.28"/>'
        "</filter>",
        f'<clipPath id="face"><circle cx="{fx:.1f}" cy="{fy:.1f}" '
        f'r="{radius:.1f}"/></clipPath>',
    ]
    photo: list[str] = []
    if payload:
        photo.append(
            f'<image href="{_data_uri(payload)}" x="{ox + inset:.1f}" '
            f'y="{oy + inset:.1f}" width="{size}" height="{size}" '
            f'clip-path="url(#face)" />'
        )
    else:
        photo.append(
            f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="{radius:.1f}" '
            f'fill="hsl({hue}, 52%, 48%)"/>'
        )
        photo.append(
            f'<text x="{fx:.1f}" y="{fy + size * 0.12:.1f}" '
            f'text-anchor="middle" fill="#ffffff" '
            f'font-size="{size * 0.34:.0f}" font-family="{_font()}" '
            f'font-weight="700">{_xml(_initials(name))}</text>'
        )
    photo.append(
        f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="{radius:.1f}" fill="none" '
        f'stroke="hsl({hue}, 78%, 58%)" stroke-width="{ring}"/>'
    )
    photo.append(
        f'<text x="{cx:.1f}" y="{oy + inset + size + band * 0.68:.1f}" '
        f'text-anchor="middle" fill="#1f2328" '
        f'font-size="{max(11, int(size * 0.2))}" font-family="{_font()}" '
        f'font-weight="700">{label}</text>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" role="img" aria-label="{_xml(name)}">\n'
        f"<title>{_xml(name)}</title>\n"
        "<defs>\n"
        + "\n".join(defs)
        + "\n</defs>\n"
        f'<g transform="rotate({tilt} {cx:.1f} {cy:.1f})" filter="url(#lift)">\n'
        f'<rect x="{ox:.1f}" y="{oy:.1f}" width="{card_w}" height="{card_h}" '
        f'rx="14" fill="#fffdf8"/>\n'
        + "\n".join(photo)
        + "\n</g>\n</svg>\n"
    )


def write_faces(
    directory: Path,
    people: list[dict[str, str]],
    avatars: Mapping[str, bytes] | None = None,
    *,
    size: int = 72,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    pictures = avatars or {}
    for index, person in enumerate(people):
        (directory / _face_file(person["login"])).write_text(
            render_sticker_svg(
                person,
                pictures.get(person["login"]),
                size=size,
                tilt=_STICKER_TILT[index % len(_STICKER_TILT)],
            ),
            encoding="utf-8",
        )
    prune_faces(directory, people)


def _kept_face_names(people: list[dict[str, str]]) -> set[str]:
    return {_face_file(person["login"]) for person in people}


def prune_faces(directory: Path, people: list[dict[str, str]]) -> None:
    if not directory.is_dir():
        return
    keep = _kept_face_names(people)
    for path in directory.glob("*.svg"):
        if path.name not in keep:
            path.unlink()


def faces_current(
    directory: Path,
    people: list[dict[str, str]],
    avatars: Mapping[str, bytes] | None = None,
    *,
    size: int = 72,
) -> bool:
    keep = _kept_face_names(people)
    if directory.is_dir():
        leftover = [path for path in directory.glob("*.svg") if path.name not in keep]
        if leftover:
            return False
    elif people:
        return False
    pictures = avatars or {}
    for index, person in enumerate(people):
        path = directory / _face_file(person["login"])
        if not path.is_file():
            return False
        expected = render_sticker_svg(
            person,
            pictures.get(person["login"]),
            size=size,
            tilt=_STICKER_TILT[index % len(_STICKER_TILT)],
        )
        if path.read_text(encoding="utf-8") != expected:
            return False
    return True


def render_html(
    people: list[dict[str, str]],
    *,
    size: int = 72,
    faces_href: str = "",
) -> str:
    """Clickable stickers. No table, so GitHub draws no grid."""
    if not people:
        return f"<p>{_xml(EMPTY_WALL)}</p>\n"
    cards = []
    prefix = faces_href.rstrip("/")
    for index, person in enumerate(people):
        login = _xml(person["login"])
        name = _xml(person["name"])
        face = _sticker_size(size, index)
        if prefix:
            src = f"{prefix}/{_face_file(person['login'])}"
            canvas_w, canvas_h = sticker_canvas(size)
            height = max(1, int(face * canvas_h / canvas_w))
        else:
            src = f"https://avatars.githubusercontent.com/{login}?s={face * 2}"
            height = face
        cards.append(
            f'<a href="https://github.com/{login}" title="{name}" '
            f'aria-label="{name}">'
            f'<img src="{src}" width="{face}" height="{height}" alt="{name}" />'
            "</a>"
        )
    return '<p align="center">\n  ' + "\n  ".join(cards) + "\n</p>\n"


def render_names(people: list[dict[str, str]]) -> str:
    if not people:
        return ""
    links = []
    for person in people:
        login = _xml(person["login"])
        name = _xml(person["name"])
        links.append(f'<a href="https://github.com/{login}">{name}</a>')
    return '<p align="center">\n  ' + "<span> · </span>".join(links) + "\n</p>\n"


def render_wall(
    people: list[dict[str, str]],
    *,
    svg_href: str = "",
    svg_width: int = 0,
    size: int = 72,
    format: str = "svg",
    faces_href: str = "",
    caption: str = "",
) -> str:
    # GitHub renders <img src="*.svg"> as one picture. The README wall is
    # one polaroid <a><img></a> per person so every face stays a link.
    # From 12 people up, also print names so a small face still has credit.
    _ = (svg_href, svg_width, format)
    count = len(people)
    if not people:
        html = f"<p>{_xml(EMPTY_WALL)}</p>\n"
    else:
        html = render_html(
            people, size=fit_readme_size(count, size), faces_href=faces_href
        )
        if count >= 12:
            html += render_names(people)
    line = (caption or "").strip()
    if line:
        html += f'<p align="center"><em>{_xml(line)}</em></p>\n'
    return html


def svg_width(
    people: list[dict[str, str]],
    size: int,
    columns: int,
    layout: str = "facepile",
    theme: str = "auto",
) -> int:
    if not people:
        return 1
    layout = fit_layout(layout, len(people))
    theme_name = parse_theme(theme)
    framed = bool(THEMES[theme_name].get("bg"))
    width, _height, _spots = _placements(
        layout, len(people), size, columns, framed
    )
    return width


def _fence_spans(text: str) -> list[tuple[int, int]]:
    """Byte offsets of fenced code blocks (``` ... ```)."""
    spans: list[tuple[int, int]] = []
    in_fence = False
    start = 0
    idx = 0
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            if not in_fence:
                in_fence = True
                start = idx
            else:
                spans.append((start, idx + len(line)))
                in_fence = False
        idx += len(line)
    return spans


def _in_span(pos: int, spans: list[tuple[int, int]]) -> bool:
    return any(lo <= pos < hi for lo, hi in spans)


def apply_readme(text: str, block: str) -> str:
    start = _start()
    end = _end()
    fences = _fence_spans(text)
    pos = 0
    while True:
        i = text.find(start, pos)
        if i < 0:
            break
        j = text.find(end, i + len(start))
        if j < 0:
            break
        if not _in_span(i, fences):
            return f"{text[:i]}{start}\n{block}{end}{text[j + len(end):]}"
        pos = i + len(start)
    raise SystemExit(
        "README is missing markers.\n\n"
        "Example comments to paste into your README:\n"
        f"{start}\n"
        f"{end}"
    )


def _emit(name: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT", "")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    return int(raw)


def _post_json(url: str, token: str, payload: dict) -> object:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "readme-contributors-action",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urlopen(req, timeout=30) as resp:
        return json.load(resp)


def model_settings() -> tuple[str, str, str] | None:
    name = os.environ.get("MODEL", "").strip()
    key = os.environ.get("MODEL_API_KEY", "").strip()
    base = os.environ.get("MODEL_BASE_URL", "").strip().rstrip("/")
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    low = name.lower()
    githubish = (
        "models.github.ai" in base
        or "models.inference.ai.azure.com" in base
        or low in {"github", "github-models"}
    )
    if githubish:
        if not (key or token):
            return None
        model = (
            name if name and low not in {"github", "github-models"} else "openai/gpt-4o-mini"
        )
        return (key or token, model, base or GITHUB_MODELS_URL)
    if not key:
        return None
    return (key, name or "gpt-4o-mini", base or "https://api.openai.com/v1")


def _is_grated(text: str) -> bool:
    low = (text or "").lower()
    if not low.strip():
        return False
    return not any(word in low for word in _UNSAFE)


_STOCK_CAPTION = (
    "showcases the",
    "dedicated individuals",
    "dedicated people",
    "valued contributors",
    "amazing contributors",
    "this contributors wall",
    "contributors wall showcases",
)


def _project_name(repo: str) -> str:
    raw = (repo or "").strip()
    if "/" in raw:
        return raw.split("/", 1)[1]
    return raw


def caption_needles(people: list[dict[str, str]], repo: str) -> set[str]:
    found: set[str] = set()
    raw = (repo or "").strip()
    if raw:
        found.add(raw.lower())
    project = _project_name(raw)
    if project:
        found.add(project.lower())
    if "/" in raw:
        owner = raw.split("/", 1)[0].strip()
        if owner:
            found.add(owner.lower())
    for person in people:
        login = str(person.get("login") or "").strip()
        name = str(person.get("name") or "").strip()
        if login:
            found.add(login.lower())
        if name:
            found.add(name.lower())
            for part in name.replace("-", " ").split():
                if len(part) >= 2:
                    found.add(part.lower())
    return {item for item in found if item}


def caption_is_specific(
    line: str, people: list[dict[str, str]], repo: str
) -> bool:
    text = (line or "").strip()
    if not _is_grated(text):
        return False
    if len(text) < 12 or len(text) > 180:
        return False
    low = text.lower()
    if any(stock in low for stock in _STOCK_CAPTION):
        return False
    needles = caption_needles(people, repo)
    if not needles:
        return False
    return any(needle in low for needle in needles)


def marked_block(text: str) -> str:
    start = _start()
    end = _end()
    fences = _fence_spans(text)
    pos = 0
    while True:
        i = text.find(start, pos)
        if i < 0:
            return ""
        j = text.find(end, i + len(start))
        if j < 0:
            return ""
        if not _in_span(i, fences):
            return text[i + len(start) : j]
        pos = i + len(start)


def existing_caption(block: str) -> str:
    match = _CAPTION_EM.search(block or "")
    if not match:
        return ""
    return html.unescape(match.group(1)).strip()


def wall_logins(block: str) -> set[str]:
    found: set[str] = set()
    for raw in _WALL_HREF.findall(block or ""):
        login = html.unescape(raw).strip().lower()
        if login:
            found.add(login)
    return found


def people_logins(people: list[dict[str, str]]) -> set[str]:
    found: set[str] = set()
    for person in people:
        login = str(person.get("login") or "").strip().lower()
        if login:
            found.add(login)
    return found


def roster_matches(people: list[dict[str, str]], block: str) -> bool:
    return people_logins(people) == wall_logins(block)


def resolve_caption(
    people: list[dict[str, str]], repo: str, readme: str = ""
) -> str:
    wanted = os.environ.get("CAPTION", "").strip()
    if wanted.lower() != "auto":
        return wanted
    if not people:
        return ""
    if readme:
        block = marked_block(readme)
        if roster_matches(people, block):
            line = existing_caption(block)
            if caption_is_specific(line, people, repo):
                print("caption reused", file=sys.stderr)
                return line
    return ask_caption(people, repo)


def ask_caption(people: list[dict[str, str]], repo: str = "") -> str:
    wanted = os.environ.get("CAPTION", "").strip()
    if wanted.lower() != "auto":
        return wanted
    if not people:
        return ""
    cfg = model_settings()
    if not cfg:
        return ""
    key, model, base = cfg
    project = _project_name(repo) or "this repository"
    roster = [
        {
            "login": str(person.get("login") or ""),
            "name": str(person.get("name") or person.get("login") or ""),
        }
        for person in people[:8]
    ]
    system = (
        "Write one muted G-rated sentence about the people on this "
        "repository's contributors wall. "
        'Reply with JSON only: {"caption": "<one sentence>"}. '
        "Name the project. You may name people from the list. "
        "Never invent names or facts. Do not write stock lines about "
        "showcasing dedicated individuals. No slurs, no adult content."
    )
    try:
        data = _post_json(
            f"{base.rstrip('/')}/chat/completions",
            key,
            {
                "model": model,
                "temperature": 0,
                "max_tokens": 80,
                "messages": [
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "repository": repo,
                                "project": project,
                                "count": len(people),
                                "people": roster,
                            }
                        ),
                    },
                ],
            },
        )
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        print(f"caption skipped: {exc}", file=sys.stderr)
        return ""
    content = ""
    if isinstance(data, dict):
        choices = data.get("choices") or []
        if choices and isinstance(choices[0], dict):
            message = choices[0].get("message")
            if isinstance(message, dict):
                content = str(message.get("content") or "")
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            return ""
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError:
            return ""
    if not isinstance(payload, dict):
        return ""
    line = str(payload.get("caption") or "").strip()
    if not caption_is_specific(line, people, repo):
        print("caption skipped: generic or unsafe", file=sys.stderr)
        return ""
    print(f"caption: {line}", file=sys.stderr)
    return line


def main() -> int:
    root = _root()
    readme = root / os.environ.get("README_PATH", "README.md")
    svg_path = root / os.environ.get("SVG_PATH", ".github/contributors.svg")
    # Actions forbids overriding GITHUB_REPOSITORY in a composite env block,
    # so the live demo passes the source repo as CONTRIBUTORS_REPO.
    repo = (
        os.environ.get("CONTRIBUTORS_REPO", "").strip()
        or os.environ.get("GITHUB_REPOSITORY", "").strip()
    )
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    fmt = os.environ.get("FORMAT", "svg").strip().lower() or "svg"
    columns = _int_env("COLUMNS", 8)
    size = _int_env("AVATAR_SIZE", 72)
    limit = _int_env("MAX_PEOPLE", 100)
    if limit <= 0:
        limit = 500
    wanted_layout = os.environ.get("LAYOUT", "auto")
    theme = parse_theme(os.environ.get("THEME", "auto"))
    check = os.environ.get("CHECK", "").strip().lower() in {"1", "true", "yes"}
    if not repo:
        raise SystemExit("GITHUB_REPOSITORY is required (owner/name)")
    people = list_people(
        repo, token, limit, exclude=os.environ.get("EXCLUDE", "")
    )
    layout = fit_layout(wanted_layout, len(people))
    faces_dir = root / os.environ.get("FACES_PATH", ".github/faces")
    avatars: dict[str, bytes] = fetch_avatars(people, token, size) if people else {}
    href = ""
    width = 0
    svg_text = ""
    if fmt == "svg":
        svg_text = render_svg(
            people,
            avatars,
            size=size,
            columns=columns,
            layout=layout,
            theme=theme,
        )
        href = Path(os.path.relpath(svg_path, start=readme.parent)).as_posix()
        if not href.startswith("."):
            href = f"./{href}"
        width = svg_width(people, size, columns, layout=layout, theme=theme)
    faces_href = Path(os.path.relpath(faces_dir, start=readme.parent)).as_posix()
    if not faces_href.startswith("."):
        faces_href = f"./{faces_href}"
    readme_text = readme.read_text(encoding="utf-8")
    block = render_wall(
        people,
        svg_href=href,
        svg_width=width,
        size=size,
        format=fmt,
        faces_href=faces_href,
        caption=resolve_caption(people, repo, readme_text),
    )
    updated = apply_readme(readme_text, block)
    same_readme = updated == readme.read_text(encoding="utf-8")
    same_svg = True
    if fmt == "svg":
        same_svg = svg_path.is_file() and svg_path.read_text(
            encoding="utf-8"
        ) == svg_text
    same_faces = faces_current(faces_dir, people, avatars, size=size)
    if same_readme and same_svg and same_faces:
        print(f"README contributors already current ({len(people)} people)")
        _emit("count", str(len(people)))
        _emit("changed", "false")
        return 0
    if check:
        print("README contributors are stale")
        _emit("count", str(len(people)))
        _emit("changed", "true")
        return 1
    if fmt == "svg":
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        svg_path.write_text(svg_text, encoding="utf-8")
    write_faces(faces_dir, people, avatars, size=size)
    readme.write_text(updated, encoding="utf-8")
    print(f"wrote {len(people)} contributors")
    _emit("count", str(len(people)))
    _emit("changed", "true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
