# JavaScript API

The element's class carries the [verse actions](../guide/actions.md) registry. Get it once
the library has loaded:

```js
const Quran = await customElements.whenDefined("quran-madina-html");
```

The registry is page-wide: every `<quran-madina-html>` tag uses it, unless its
[`actions`](attributes.md) attribute picks a subset. Changes apply at once to the tags already
on the page.

## Functions

| Function | Returns | Does |
|---|---|---|
| `Quran.registerAction(action)` | the id | Adds an action, or replaces the one with the same id. Throws a `TypeError` if `action` is malformed. |
| `Quran.unregisterAction(id)` | `true` if it was there | Removes one action. `"copy"` and `"translate"` can be removed too. |
| `Quran.clearActions()` | | Removes every action, the built-ins too. Verses become plain text. |
| `Quran.resetActions()` | | Back to the built-in copy and translate. |
| `Quran.actions` | `[{id, title, order}]` | The registered actions, in popup order. |

The React wrapper exports the same functions (`registerAction`, `unregisterAction`,
`clearActions`, `resetActions`; each returns a promise, since it waits for the library), and a
`useAyaAction(action)` hook that registers an action while a component is mounted.

## An action

| Field | Required | Value |
|---|---|---|
| `id` | yes | Unique id. `copy` and `translate` are the built-ins. |
| `onSelect(aya)` | yes | Runs when the button is clicked; the popup closes first. |
| `title` | | Tooltip and accessible name. Default: the id. |
| `icon` | | SVG markup, an image URL, a DOM element, or a function returning one. Default: the title as text. |
| `order` | | Position in the popup, smallest first. Copy is 10, translate 20. Default: 100. |
| `when(aya)` | | Offer the action only where this returns true. |

## The verse (`aya`)

What `onSelect` and `when` get:

| Field | Value |
|---|---|
| `sura` | Sura number, 1–114. |
| `aya` | Verse number. |
| `page` | The Mushaf page of the verse in the current print. |
| `text` | The verse text (read on demand). |
| `suraName` | The sura's name. |
| `layout` | `1441H`, `1405H` or `IndoPak`. |
| `tag` | The `<quran-madina-html>` element. |
| `element` | The clicked line piece of the verse. |
| `close()` | Closes the popup. |

## Properties

Every [tag attribute](attributes.md) is also a property: `tag.aya = 256` sets `aya="256"`.
`tag.actions` takes a string or an array: `["copy"]` sets `actions="copy"`, and `[]` sets
`actions="none"`.
