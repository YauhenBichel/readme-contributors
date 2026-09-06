# Security Policy

## Reporting a vulnerability

Open a **public** GitHub issue on this repo. Label it `security` if you can.

Include:

- what the issue is and where in the code it lives
- how to reproduce it
- what an attacker could do with it

Do **not** paste live API keys, tokens, or `.env` contents into the issue.

## Scope

In scope:

- a generated README that injects unescaped HTML from a display name
- a workflow example that checks out untrusted pull-request code with
  write permission
- secrets committed to the repository

Out of scope:

- GitHub drawing a border on someone else's table
- avatar taste
