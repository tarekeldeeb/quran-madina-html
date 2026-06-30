# Security Policy

## Supported Versions

Security fixes are applied to the latest `0.6.x` line and published to npm
(`quran-madina-html` and `@tarekeldeeb/quran-madina-react`).

| Version | Supported          |
| ------- | ------------------ |
| 0.6.x   | :white_check_mark: |
| < 0.6   | :x:                |

Always upgrade to the most recent release before reporting an issue.

## Scope

What ships to consumers is intentionally small, which limits the attack surface:

- **Core (`quran-madina-html`)** — the published package contains only the built
  `dist/` runtime, the `assets/` (JSON databases, fonts), and a single runtime
  dependency (`x-tag`). It renders pre-computed data into the DOM; it does not
  execute remote code or evaluate user input as code.
- **React wrapper (`@tarekeldeeb/quran-madina-react`)** — published as a thin
  built wrapper with **no runtime dependencies** (React is a peer dependency).

Advisories against **build/test tooling** (e.g. grunt, vite, esbuild, vitest)
are dev-only `devDependencies` and are **not** part of either published package,
so they do not affect consumers. We still keep them patched.

## Reporting a Vulnerability

Please report security issues **privately** — do not open a public issue for an
unpatched vulnerability.

1. Preferred: GitHub **private vulnerability reporting** — open the repository's
   **Security** tab and choose **"Report a vulnerability"**
   (https://github.com/tarekeldeeb/quran-madina-html/security/advisories/new).
2. Alternatively, contact the maintainer (Tarek Eldeeb) through the email listed
   on the GitHub profile.

When reporting, include the affected version, a description, and a minimal
reproduction if possible.

We aim to acknowledge reports within a few days and, for accepted issues, to
release a patch on the supported `0.6.x` line and credit the reporter (unless
anonymity is requested). Reports that are out of scope (e.g. dev-only tooling
advisories) will be explained and closed.
