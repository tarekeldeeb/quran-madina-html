# Script options

Attributes of the `<script>` tag that loads the library. They apply to every tag on the page.

```html
<script src="https://unpkg.com/quran-madina-html@2"
        data-layout="1441H" data-font-size="16"></script>
```

| Attribute | Value | Default | Description |
|---|---|---|---|
| `data-layout` | `1441H`, `1405H`, `IndoPak` | `1441H` | Which print. Not case sensitive; unknown values fall back to `1441H`. [Guide](../guide/layouts.md) |
| `data-font-size` | 6–100 (px) | `16` | Size of the text. Decimals allowed. |
| `data-cdn` | a URL (absolute or relative) | unpkg | Where the CSS, databases and fonts load from; a trailing `/` is added. `javascript:`, `data:` and `vbscript:` values are refused (console warning, default used). [Guide](../guide/self-hosting.md) |
| `data-font`, `data-name` | | | 1.x options, ignored since 2.0 with a console warning. |

## Versions on unpkg

| `src` | Loads |
|---|---|
| `https://unpkg.com/quran-madina-html@2` | the latest 2.x (recommended) |
| `https://unpkg.com/quran-madina-html@2.1.0` | exactly 2.1.0 |
| `https://unpkg.com/quran-madina-html@1` | the 1.x renderer ([its docs](../v1.md)) |
