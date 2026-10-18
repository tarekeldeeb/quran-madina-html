# Releasing

One run of the **Release** workflow publishes everything, under one version number:

| Package | Registry |
|---|---|
| `quran-madina-html` | npm |
| `@tarekeldeeb/quran-madina-react` | npm |
| `quran_madina_flutter` | pub.dev |

## Run a release

1. Merge everything into `main`.
2. Open [Actions → Release](https://github.com/tarekeldeeb/quran-madina-html/actions/workflows/release.yml)
   and choose **Run workflow** (this works from a phone too).
3. Pick the version bump (`patch`, `minor` or `major`), and leave **dry run** ticked.
4. Check the dry run's log, then run it again with dry run off.

The release builds `dist/`, bumps the version (the wrappers follow), commits, tags (e.g.
`2.1.1`), creates the GitHub release, and publishes both npm packages. The tag then starts
**Publish Flutter package**, which publishes to pub.dev.

**wrapper only** republishes just the React wrapper at the current version, for when the core
package published but the wrapper didn't.

## Secrets

| Secret | Needed for | What it is |
|---|---|---|
| `NPM_TOKEN` | npm | A granular npm token with read and write on both packages, allowed to bypass two-factor authentication. |
| `RELEASE_PAT` | pub.dev | A fine-grained GitHub token for this repository with Contents read and write. Without it, the release tag doesn't start the pub.dev workflow. |

pub.dev needs no secret: the package's admin page trusts this repository's workflow for tags
matching `{{version}}`.

## Docs and demo

- These docs publish from `main` on every change to `docs/` or `mkdocs.yml` (the **Docs**
  workflow), into the `docs/` folder of the GitHub Pages site.
- The Flutter web example publishes from `main` on every change to `flutter/` or the library
  (the **Flutter web example** workflow), into the `flutter/` folder.
- The demo (`demo/`) lives on the same `gh-pages` branch. When updating it by hand, keep the
  `docs/` and `flutter/` folders.
