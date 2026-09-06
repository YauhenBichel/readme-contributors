# README contributors

[![CI](https://github.com/YauhenBichel/readme-contributors/actions/workflows/ci.yml/badge.svg)](https://github.com/YauhenBichel/readme-contributors/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](./LICENSE)
[![good first issue](https://img.shields.io/github/issues/YauhenBichel/readme-contributors/good%20first%20issue)](https://github.com/YauhenBichel/readme-contributors/labels/good%20first%20issue)

A composite GitHub Action that fills a circular-avatar contributors wall
into a README. It reads the GitHub contributors API, omits bots, and
replaces a pair of HTML markers.

GitHub draws a border on every README `<table>`. This Action does not
use a table. The default is a self-contained SVG facepile (circular
avatars, light and dark rings) plus a linked name row so each person
stays clickable.

Used by [py-harness](https://github.com/YauhenBichel/py-harness). Issues
and pull requests belong **here**.

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
      - uses: YauhenBichel/readme-contributors@v1
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
      - run: |
          git config user.name github-actions[bot]
          git config user.email 41898282+github-actions[bot]@users.noreply.github.com
          git add README.md .github/contributors.svg
          git diff --cached --quiet && exit 0
          git commit -m "docs: refresh README contributors"
          git push
```

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
| `format` | `svg` | `svg` for the circular wall, `html` for linked avatars only |
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
