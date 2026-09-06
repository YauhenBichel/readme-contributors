#!/usr/bin/env python3
"""Fill a README contributors wall from the GitHub API.

Bots are omitted. The default drawing is a circular facepile SVG so the
README does not pick up GitHub's table borders. A linked name row under
the picture keeps every person clickable. Layouts and themes change the
drawing; they do not change who is listed.
"""

from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path
from typing import Mapping
from urllib.error import URLError
from urllib.request import Request, urlopen

API = "https://api.github.com"
AVATARS = "https://avatars.githubusercontent.com"
DEFAULT_START = "<!-- readme: contributors,bots/- -start -->"
DEFAULT_END = "<!-- readme: contributors,bots/- -end -->"
# 1x1 PNG used only when a test injects a known image.
TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)
LAYOUTS = ("facepile", "grid", "tiles", "list", "compact")
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


def list_people(repo: str, token: str, limit: int = 48) -> list[dict[str, str]]:
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
            if not login or kind == "Bot" or login.endswith("[bot]"):
                continue
            profile = _get(f"{API}/users/{login}", token)
            name = login
            if isinstance(profile, dict) and profile.get("name"):
                name = str(profile["name"])
            people.append({"login": login, "name": name})
        if len(rows) < 100:
            break
        page += 1
    return people


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
    name = (raw or "facepile").strip().lower() or "facepile"
    if name not in LAYOUTS:
        allowed = ", ".join(LAYOUTS)
        raise SystemExit(f"layout must be one of: {allowed}")
    return name


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


def _metrics(
    layout: str,
    size: int,
    columns: int,
    count: int,
    *,
    framed: bool,
) -> dict[str, int]:
    columns = max(1, columns)
    size = max(32, size)
    if layout == "facepile":
        pad = 10 if framed else 4
        step = int(size * 0.64)
        row_gap = 14
        name_w = 0
    elif layout == "compact":
        pad = 10 if framed else 6
        step = size + 6
        row_gap = 6
        name_w = 0
    elif layout == "list":
        columns = 1
        pad = 14 if framed else 12
        step = 1
        row_gap = 10
        name_w = 168
    elif layout == "tiles":
        pad = 14 if framed else 10
        step = size + 14
        row_gap = 14
        name_w = 0
    else:
        pad = 12 if framed else 8
        step = size + 12
        row_gap = 12
        name_w = 0
    rows = (count + columns - 1) // columns if count else 1
    widest = min(columns, count) if count else 1
    if layout == "list":
        width = pad * 2 + size + 14 + name_w
        height = pad * 2 + size * count + row_gap * max(0, count - 1)
    elif layout == "facepile":
        width = pad * 2 + size + step * max(0, widest - 1)
        height = pad * 2 + size * rows + row_gap * max(0, rows - 1)
    else:
        width = pad * 2 + step * max(0, widest - 1) + size
        height = pad * 2 + (size + row_gap) * max(0, rows - 1) + size
    return {
        "columns": columns,
        "size": size,
        "pad": pad,
        "step": step,
        "row_gap": row_gap,
        "rows": rows,
        "widest": widest,
        "width": max(1, width),
        "height": max(1, height),
        "name_w": name_w,
    }


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
    """Draw the wall. Names stay in the HTML row so each face stays a link."""
    layout = parse_layout(layout)
    theme_name = parse_theme(theme)
    palette = THEMES[theme_name]
    if not people:
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1">'
            "</svg>\n"
        )
    pictures = avatars or {}
    framed = bool(palette.get("bg"))
    metrics = _metrics(layout, size, columns, len(people), framed=framed)
    size = metrics["size"]
    columns = metrics["columns"]
    pad = metrics["pad"]
    step = metrics["step"]
    row_gap = metrics["row_gap"]
    width = metrics["width"]
    height = metrics["height"]
    names = ", ".join(person["name"] for person in people)
    defs: list[str] = _theme_css(palette)
    body: list[str] = []
    if palette.get("bg"):
        body.append(
            f'<rect width="{width}" height="{height}" rx="16" '
            f'fill="{palette["bg"]}"/>'
        )
    shape = "tile" if layout == "tiles" else "circle"
    order = (
        reversed(list(enumerate(people)))
        if layout == "facepile"
        else enumerate(people)
    )
    for index, person in order:
        if layout == "list":
            x = float(pad)
            y = float(pad + index * (size + row_gap))
        else:
            column = index % columns
            row = index // columns
            x = float(pad + column * step)
            y = float(pad + row * (size + row_gap))
        if layout == "list" and palette.get("card"):
            body.append(
                f'<rect x="{pad - 4:.1f}" y="{y - 4:.1f}" '
                f'width="{width - pad * 2 + 8}" height="{size + 8}" '
                f'rx="12" fill="{palette["card"]}"/>'
            )
        _paint_face(
            defs,
            body,
            index=index,
            person=person,
            pictures=pictures,
            x=x,
            y=y,
            size=size,
            shape=shape,
        )
        if layout == "list":
            login = _xml(person["login"])
            label = _xml(person["name"])
            body.append(
                f'<text class="label" x="{x + size + 14:.1f}" '
                f'y="{y + size * 0.42:.1f}" font-size="15">{label}</text>'
            )
            body.append(
                f'<text class="muted" x="{x + size + 14:.1f}" '
                f'y="{y + size * 0.72:.1f}" font-size="12">@{login}</text>'
            )
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


def render_html(
    people: list[dict[str, str]],
    *,
    size: int = 72,
) -> str:
    """Linked avatars that wrap. No table, so GitHub draws no grid."""
    if not people:
        return ""
    faces = []
    for person in people:
        login = _xml(person["login"])
        name = _xml(person["name"])
        faces.append(
            f'<a href="https://github.com/{login}" title="{name}">'
            f'<img src="https://avatars.githubusercontent.com/{login}'
            f'?s={size * 2}" width="{size}" height="{size}" alt="{name}" />'
            "</a>"
        )
    return '<p align="center">\n  ' + "\n  ".join(faces) + "\n</p>\n"


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
) -> str:
    names = render_names(people)
    if format == "html" or not svg_href:
        return render_html(people, size=size) + names
    alt = _xml(", ".join(person["name"] for person in people) or "Contributors")
    width = f' width="{svg_width}"' if svg_width else ""
    picture = (
        f'<p align="center">\n'
        f'  <img src="{_xml(svg_href)}"{width} alt="{alt}" />\n'
        f"</p>\n"
    )
    return picture + names


def svg_width(
    people: list[dict[str, str]],
    size: int,
    columns: int,
    layout: str = "facepile",
    theme: str = "auto",
) -> int:
    if not people:
        return 1
    layout = parse_layout(layout)
    theme_name = parse_theme(theme)
    framed = bool(THEMES[theme_name].get("bg"))
    return _metrics(layout, size, columns, len(people), framed=framed)["width"]


def apply_readme(text: str, block: str) -> str:
    start = _start()
    end = _end()
    if start not in text or end not in text:
        raise SystemExit(f"README is missing {start} / {end}")
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    return f"{before}{start}\n{block}{end}{after}"


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


def main() -> int:
    root = _root()
    readme = root / os.environ.get("README_PATH", "README.md")
    svg_path = root / os.environ.get("SVG_PATH", ".github/contributors.svg")
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    fmt = os.environ.get("FORMAT", "svg").strip().lower() or "svg"
    columns = _int_env("COLUMNS", 8)
    size = _int_env("AVATAR_SIZE", 72)
    limit = _int_env("MAX_PEOPLE", 48)
    layout = parse_layout(os.environ.get("LAYOUT", "facepile"))
    theme = parse_theme(os.environ.get("THEME", "auto"))
    check = os.environ.get("CHECK", "").strip().lower() in {"1", "true", "yes"}
    if not repo:
        raise SystemExit("GITHUB_REPOSITORY is required (owner/name)")
    people = list_people(repo, token, limit)
    avatars: dict[str, bytes] = {}
    href = ""
    width = 0
    svg_text = ""
    if fmt == "svg":
        avatars = fetch_avatars(people, token, size)
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
    block = render_wall(
        people,
        svg_href=href,
        svg_width=width,
        size=size,
        format=fmt,
    )
    updated = apply_readme(readme.read_text(encoding="utf-8"), block)
    same_readme = updated == readme.read_text(encoding="utf-8")
    same_svg = True
    if fmt == "svg":
        same_svg = svg_path.is_file() and svg_path.read_text(
            encoding="utf-8"
        ) == svg_text
    if same_readme and same_svg:
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
    readme.write_text(updated, encoding="utf-8")
    print(f"wrote {len(people)} contributors")
    _emit("count", str(len(people)))
    _emit("changed", "true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
