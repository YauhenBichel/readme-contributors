# README contributors

[![CI](https://github.com/YauhenBichel/readme-contributors/actions/workflows/ci.yml/badge.svg)](https://github.com/YauhenBichel/readme-contributors/actions/workflows/ci.yml)
[![Contributors](https://img.shields.io/github/contributors/YauhenBichel/readme-contributors)](https://github.com/YauhenBichel/readme-contributors/graphs/contributors)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](./LICENSE)
[![GitHub Marketplace](https://img.shields.io/badge/GitHub%20Marketplace-v1.5.1-6e5494)](https://github.com/marketplace/actions/readme-contributors)
[![Examples](https://img.shields.io/badge/examples-GitHub%20Pages-0969da)](https://yauhenbichel.github.io/readme-contributors/)
Marketplace: [readme-contributors](https://github.com/marketplace/actions/readme-contributors) · Site: [yauhenbichel.github.io/readme-contributors](https://yauhenbichel.github.io/readme-contributors/)

[![good first issue](https://img.shields.io/github/issues/YauhenBichel/readme-contributors/good%20first%20issue)](https://github.com/YauhenBichel/readme-contributors/labels/good%20first%20issue)

A **GitHub Action** that draws a **contributors** wall into your
**README**: one clickable **polaroid sticker** per person (face plus
name), plus SVG layouts for Pages (facepile, stickers, grid, tiles,
orbit, honeycomb, and more). It reads the GitHub contributors API,
omits bots, and replaces a pair of HTML markers. No `<table>`, so
GitHub does not draw a grid. No third-party list service.

[![18s demo](./docs/media/readme-contributors-demo.gif)](https://yauhenbichel.github.io/readme-contributors/#demo)

## What

A **GitHub Action** that fills a README with the people who actually
committed. Each person is a **polaroid**: face, name, a bit of tilt.
Each card is its own link. Bots are omitted. No `<table>`. No
third-party list service.

Watch the 18s demo (GitHub README plays this as a GIF; the MP4 is on
[Pages](https://yauhenbichel.github.io/readme-contributors/#demo)):

[![18s demo: polaroid wall in real READMEs](./docs/media/readme-contributors-demo.gif)](https://yauhenbichel.github.io/readme-contributors/#demo)

## Why

GitHub cannot click a face inside one SVG. One picture is one link.
A `wall.svg` with six heads looks clickable. It is not.

This Action writes one card per person. Tap it, you land on their
GitHub profile.

## How

1. Put markers in `README.md`:

```markdown
<!-- readme: contributors,bots/- -start -->
<!-- readme: contributors,bots/- -end -->
```

2. Call the Action. Pin the tag to read. Pin the SHA if the job can write:

```yaml
- uses: YauhenBichel/readme-contributors@635c6ff57a4c155e285b6efa75df3c3b0da7f1df # v1.5.1
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
    format: html
```

3. Commit the rewritten README and `.github/faces`.

A full copy-paste job is in
[examples/contributors.yml](./examples/contributors.yml).
The Pages how-to is
[yauhenbichel.github.io/readme-contributors](https://yauhenbichel.github.io/readme-contributors/#use).

## Examples

- Live tap-the-cards wall:
  [yauhenbichel.github.io/readme-contributors/#live](https://yauhenbichel.github.io/readme-contributors/#live)
- [YauhenBichel/py-harness](https://github.com/YauhenBichel/py-harness) — 6 people, this demo wall
- [MoleCare/molecare-mcp](https://github.com/MoleCare/molecare-mcp) — different 6 people
- [MoleCare/molecare-skin-llm](https://github.com/MoleCare/molecare-skin-llm)
- [MoleCare/molecare-ml](https://github.com/MoleCare/molecare-ml)
- [MoleCare/molecare-desktop](https://github.com/MoleCare/molecare-desktop)

MoleCare repos are open source. Not a medical device.

## Live demo

This wall is produced by **this Action**, live, from the
[py-harness](https://github.com/YauhenBichel/py-harness) contributors
API (bots omitted). It refreshes on a schedule. That is the picture
other repositories get.

<!-- demo: live -start -->
<p align="center">
  <a href="https://github.com/YauhenBichel" title="Yauhen Bichel"><img src=".github/faces/YauhenBichel.svg" width="87" height="99" alt="Yauhen Bichel" /></a>
  <a href="https://github.com/xianjianlf2" title="Mark Xian"><img src=".github/faces/xianjianlf2.svg" width="66" height="75" alt="Mark Xian" /></a>
  <a href="https://github.com/ItzSaurav" title="Itzsaurav"><img src=".github/faces/ItzSaurav.svg" width="72" height="82" alt="Itzsaurav" /></a>
  <a href="https://github.com/svkzn" title="svkzn"><img src=".github/faces/svkzn.svg" width="80" height="91" alt="svkzn" /></a>
  <a href="https://github.com/Aditya-233" title="Aditya"><img src=".github/faces/Aditya-233.svg" width="63" height="72" alt="Aditya" /></a>
  <a href="https://github.com/kkkhs" title="Huangshuo Kuang"><img src=".github/faces/kkkhs.svg" width="76" height="87" alt="Huangshuo Kuang" /></a>
</p>
<!-- demo: live -end -->

Examples for every layout live on the
[GitHub Pages site](https://yauhenbichel.github.io/readme-contributors/).
Issues and pull requests belong **here**.

## Used by

These public repositories pin this Action on their **default branch**.
GitHub does not show a Used-by graph for Actions, so this list is the
source of truth.

- [YauhenBichel/py-harness](https://github.com/YauhenBichel/py-harness) — everyday laptop harness. The live demo above is its wall.
- [YauhenBichel/merge-cheer](https://github.com/YauhenBichel/merge-cheer) — merge-celebration Action.
- [YauhenBichel/readme-contributors](https://github.com/YauhenBichel/readme-contributors) — this repository (dogfood).
- [MoleCare/molecare-mcp](https://github.com/MoleCare/molecare-mcp)
- [MoleCare/molecare-skin-llm](https://github.com/MoleCare/molecare-skin-llm)
- [MoleCare/molecare-ml](https://github.com/MoleCare/molecare-ml)
- [MoleCare/molecare-desktop](https://github.com/MoleCare/molecare-desktop)

[Search every public workflow that pins it](https://github.com/search?q=YauhenBichel%2Freadme-contributors%40+path%3A.github%2Fworkflows&type=code).

## Layouts

Set `layout`. The default stays the overlapping facepile. The README
wall is always the clickable polaroids; `layout` changes the SVG
drawn for Pages.

**stickers** — tilted cards with a chunky ring and a drop shadow.

<p align="center">
  <img src="./docs/layout-stickers.svg" alt="stickers layout" />
</p>

**grid** — spaced circles, one row until `columns`.

<p align="center">
  <img src="./docs/layout-grid.svg" width="460" alt="grid layout" />
</p>

**tiles** — rounded squares.

<p align="center">
  <img src="./docs/layout-tiles.svg" width="474" alt="tiles layout" />
</p>

**list** — avatar, name, and login on each row.

<p align="center">
  <img src="./docs/layout-list.svg" width="270" alt="list layout" />
</p>

**compact** — a tighter grid for a long list.

<p align="center">
  <img src="./docs/layout-compact.svg" width="378" alt="compact layout" />
</p>

**wave** — a sine-staggered row.

<p align="center">
  <img src="./docs/layout-wave.svg" alt="wave layout" />
</p>

**orbit** — first person in the middle, the rest on a ring.

<p align="center">
  <img src="./docs/layout-orbit.svg" alt="orbit layout" />
</p>

**honeycomb** — hex tiles on offset rows.

<p align="center">
  <img src="./docs/layout-honeycomb.svg" alt="honeycomb layout" />
</p>

**ribbon** — a zipper that steps up and down.

<p align="center">
  <img src="./docs/layout-ribbon.svg" alt="ribbon layout" />
</p>

**constellation** — faces with faint links between neighbours.

<p align="center">
  <img src="./docs/layout-constellation.svg" alt="constellation layout" />
</p>

**banner** — the first person is larger; the others sit beside them.

<p align="center">
  <img src="./docs/layout-banner.svg" alt="banner layout" />
</p>

```yaml
- uses: YauhenBichel/readme-contributors@v1.5.1
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
    layout: tiles
```

## Themes

Set `theme`. `auto` follows the reader's light or dark README. The
others paint a frame so the wall stays the same in both.

<p align="center">
  <img src="./docs/theme-midnight.svg" width="284" alt="midnight theme" />
  <img src="./docs/theme-sunrise.svg" width="284" alt="sunrise theme" />
</p>
<p align="center">
  <img src="./docs/theme-forest.svg" width="284" alt="forest theme" />
  <img src="./docs/theme-ocean.svg" width="284" alt="ocean theme" />
</p>
<p align="center">
  <img src="./docs/theme-mono.svg" width="284" alt="mono theme" />
</p>

```yaml
- uses: YauhenBichel/readme-contributors@v1.5.1
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
    layout: facepile
    theme: midnight
```

`theme` accepts `auto`, `github`, `midnight`, `sunrise`, `forest`,
`ocean`, or `mono`.

## Use it

Add markers to your README:

```markdown
## Contributors

Thank you to everyone who has helped.

<!-- readme: contributors,bots/- -start -->
<!-- readme: contributors,bots/- -end -->
```

Then call the Action. Pin it to a commit SHA when the job has
`contents: write`.

```yaml
name: Contributors

on:
  schedule:
    - cron: "17 4 * * 0"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  readme:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: YauhenBichel/readme-contributors@635c6ff57a4c155e285b6efa75df3c3b0da7f1df # v1.5.1
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          # layout: tiles
          # theme: midnight
      - run: |
          git config user.name github-actions[bot]
          git config user.email 41898282+github-actions[bot]@users.noreply.github.com
          git add README.md .github/contributors.svg .github/faces
          git diff --cached --quiet && exit 0
          git commit -m "docs: refresh README contributors"
          git push
```

A copy-paste workflow that opens a pull request on a protected default
branch is in [examples/contributors.yml](./examples/contributors.yml).
The Action only writes files in the workspace. Your workflow decides
whether to commit them.

## Contribute

This repository is public and Apache-2.0. Fork it, pick a
[`good first issue`](https://github.com/YauhenBichel/readme-contributors/labels/good%20first%20issue),
and open a pull request. See [CONTRIBUTING.md](./CONTRIBUTING.md).

```bash
git clone https://github.com/YauhenBichel/readme-contributors.git
cd readme-contributors
python3 -m unittest discover -s tests -q
```

No token, no GPU, no extra packages. `fill.py` is stdlib only.

## Inputs

| Input | Default | Meaning |
| --- | --- | --- |
| `readme` | `README.md` | File that holds the markers |
| `svg` | `.github/contributors.svg` | Generated wall (when `format` is `svg`) |
| `faces` | `.github/faces` | One polaroid SVG per person |
| `format` | `svg` | README icons always link to profiles; `html` skips the combined SVG file |
| `layout` | `facepile` | `facepile`, `stickers`, `grid`, `tiles`, `list`, `compact`, `wave`, `orbit`, `honeycomb`, `ribbon`, `constellation`, `banner` |
| `theme` | `auto` | `auto`, `github`, `midnight`, `sunrise`, `forest`, `ocean`, `mono` |
| `columns` | `8` | Faces per row |
| `avatar-size` | `72` | Face diameter, pixels |
| `max` | `48` | Cap after bots are omitted |
| `repository` | the current repo | `owner/name` to read |
| `token` | `github.token` | Raises the API rate limit |
| `check` | `false` | Exit 1 if the files would change |
| `marker-start` / `marker-end` | the comments above | Override the markers |

## Outputs

| Output | Meaning |
| --- | --- |
| `count` | People written |
| `changed` | `true` when the README or SVG was rewritten |

## Locally

```bash
GITHUB_REPOSITORY=owner/name GITHUB_TOKEN="$GITHUB_TOKEN" \
  python3 fill.py
```

Set `CHECK=true` for the `check` input.

## Contributors

Thank you to everyone who has helped this Action.

<!-- readme: contributors,bots/- -start -->
<p align="center">
  <a href="https://github.com/YauhenBichel" title="Yauhen Bichel"><img src=".github/faces/YauhenBichel.svg" width="87" height="99" alt="Yauhen Bichel" /></a>
  <a href="https://github.com/HeaTTap" title="HeaTTap"><img src=".github/faces/HeaTTap.svg" width="66" height="75" alt="HeaTTap" /></a>
</p>
<!-- readme: contributors,bots/- -end -->

Filled from GitHub commits (bots omitted).
