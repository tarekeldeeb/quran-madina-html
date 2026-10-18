# Development

The repository has two halves:

- **The runtime** (`src/quran-madina-html.js` and `.css`): the script that defines the tag and
  renders from the databases.
- **The database builder** (`src/db/`, Python): an offline pipeline that produces the
  databases in `assets/db/v2`. Users never run it.

Plus the wrappers in `react/` and `flutter/`, and these docs in `docs/`.

- [Setup and tests](setup.md)
- [Building the databases](databases.md)
- [Releasing](releasing.md)
- Design notes for version 2: [design decisions](../v2/design-decisions.md),
  [phase 0 audit](../v2/phase0-audit.md), [phase 1 proof of concept](../v2/phase1-poc.md).
