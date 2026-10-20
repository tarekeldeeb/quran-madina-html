# Security Policy

## Supported Versions

Security fixes are applied to the latest `2.x` release and published with it: npm
(`quran-madina-html`, `@tarekeldeeb/quran-madina-react`,
`@tarekeldeeb/quran-madina-react-native`), pub.dev (`quran_madina_flutter`) and the WordPress
plugin zip on the GitHub release.

| Version | Supported          |
| ------- | ------------------ |
| 2.x     | :white_check_mark: |
| < 2.0   | :x:                |

Always upgrade to the most recent release before reporting an issue.

## Scope

What ships to consumers is intentionally small, which limits the attack surface:

- **Core (`quran-madina-html`)** — the published package contains only the built
  `dist/` runtime and the `assets/` (JSON databases, fonts), with **no runtime
  dependencies** (the custom element is registered via the native browser
  Custom Elements v1 API). It renders pre-computed data into the DOM; it does
  not execute remote code or evaluate user input as code.
- **React wrapper (`@tarekeldeeb/quran-madina-react`)** — published as a thin
  built wrapper with **no runtime dependencies** (React is a peer dependency).
- **React Native wrapper (`@tarekeldeeb/quran-madina-react-native`)** — plain
  JavaScript with **no runtime dependencies** (React, React Native and
  react-native-webview are peer dependencies).
- **Flutter package (`quran_madina_flutter`)** — depends only on the Flutter SDK,
  `webview_flutter` and `web`.
- **WordPress plugin** — PHP with no third-party code besides its copy of the
  library above.

Advisories against **build/test tooling** (e.g. release-it, jshint, http-server,
vite, esbuild, vitest) are dev-only `devDependencies` and are **not** part of any
published package, so they do not affect consumers. We still keep them patched.

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
release a patch on the supported `2.x` line and credit the reporter (unless
anonymity is requested). Reports that are out of scope (e.g. dev-only tooling
advisories) will be explained and closed.
