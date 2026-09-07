# Contributing

Thanks for being here. This Action is small on purpose: one Python file,
stdlib only, no table in the README it writes.

## Rules that are not negotiable

- Do not add a third-party list service or a `curl | sh` install.
- Do not draw the wall as a `<table>`. GitHub borders every table.
- Do not commit tokens, `.env`, or live hostnames.
- Display names from the API are untrusted. Escape them.

## Getting set up

```bash
git clone https://github.com/YauhenBichel/readme-contributors.git
cd readme-contributors
python3 -m unittest discover -s tests -q
```

You do not need a GitHub token to run the tests. The renderer is
exercised with fixture people.

## What you may add

- A test that fails today and a small change that makes it pass
- An input that stays optional and has a default
- Docs that show a copy-paste workflow, not an essay

## Before you open a pull request

- [ ] `python3 -m unittest discover -s tests -q` passes
- [ ] One concern per PR
- [ ] No secrets or personal paths

## Pick an issue

Start at [`good first issue`](https://github.com/YauhenBichel/readme-contributors/labels/good%20first%20issue).
If that list is empty, this one is ready:

1. When the README markers are missing, print both comments so they can be pasted.

Design questions go in the issue thread.

py-harness runs a copy of this Action. Land the change here first.

## Licence

By contributing you agree that your contributions are licensed under the
[Apache-2.0 licence](./LICENSE) that covers this project.
