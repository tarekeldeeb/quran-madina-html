"""Render README.md as the GitHub Pages landing page (index.html at the site root).

    python scripts/readme_page.py [out.html]      # default: site-root/index.html

The page is the README itself, styled for reading, in light and dark. Links the README makes
to files in the repository point to GitHub; links into the site (docs, demo) stay as they are.
Run by .github/workflows/docs.yml, which publishes the page with the docs.
"""
import os
import re
import sys

import markdown
from pygments.formatters import HtmlFormatter  # pylint: disable=no-name-in-module

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REPO = "https://github.com/tarekeldeeb/quran-madina-html"
SITE = "https://tarekeldeeb.github.io/quran-madina-html/"

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="icon" href="favicon.ico">
<style>
:root {{
  --bg: #ffffff; --fg: #1f2328; --muted: #59636e; --line: #d1d9e0; --code-bg: #f6f8fa;
  --link: #00796b; --top: #00796b;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #0d1117; --fg: #e6edf3; --muted: #9198a1; --line: #3d444d; --code-bg: #151b23;
    --link: #4db6ac; --top: #004d40;
  }}
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: var(--bg); color: var(--fg);
  font: 16px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans", sans-serif;
}}
.top {{
  display: flex; flex-wrap: wrap; gap: 6px 20px; align-items: center;
  padding: 10px 20px; background: var(--top); color: #fff; font-size: 15px;
}}
.top a {{ color: #fff; text-decoration: none; }}
.top a:hover {{ text-decoration: underline; }}
.top .brand {{ font-weight: 600; margin-right: auto; }}
main {{ max-width: 860px; margin: 0 auto; padding: 24px 20px 64px; }}
a {{ color: var(--link); }}
h1 {{ font-size: 2em; margin: 0.4em 0 0.5em; padding-bottom: 0.3em; border-bottom: 1px solid var(--line); }}
h2 {{ margin-top: 1.8em; padding-bottom: 0.3em; border-bottom: 1px solid var(--line); }}
h3 {{ margin-top: 1.4em; }}
img {{ max-width: 100%; height: auto; }}
p > a > img {{ vertical-align: middle; }}
code {{
  font: 0.88em/1.4 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  background: var(--code-bg); padding: 0.15em 0.35em; border-radius: 6px;
}}
pre {{ background: var(--code-bg); padding: 14px 16px; border-radius: 8px; overflow-x: auto; }}
pre code {{ background: none; padding: 0; }}
ul {{ padding-left: 1.4em; }}
li {{ margin: 0.25em 0; }}
footer {{ margin-top: 3em; color: var(--muted); font-size: 0.9em; }}
{pygments_light}
@media (prefers-color-scheme: dark) {{
{pygments_dark}
}}
</style>
</head>
<body>
<nav class="top">
  <a class="brand" href="{site}">quran-madina-html</a>
  <a href="{site}docs/">Docs</a>
  <a href="{site}reader/">Quran reader</a>
  <a href="{site}demo/index.html">Live demo</a>
  <a href="{repo}">GitHub</a>
</nav>
<main>
{body}
<footer>This page is the project's <a href="{repo}#readme">README</a>.</footer>
</main>
</body>
</html>
"""


def fix_links(html):
    """Point relative links and images at the repository on GitHub."""
    def repl(match):
        attr, url = match.group(1), match.group(2)
        if re.match(r"^(https?:|mailto:|#|/)", url):
            return match.group(0)
        kind = "raw/main" if attr == "src" else "blob/main"
        return f'{attr}="{REPO}/{kind}/{url}"'
    return re.sub(r'(href|src)="([^"]*)"', repl, html)


def render(text):
    """The README's title, description and body HTML."""
    body = markdown.markdown(
        text, extensions=["fenced_code", "codehilite", "tables", "md_in_html"],
        extension_configs={"codehilite": {"guess_lang": False, "css_class": "highlight"}})
    title = re.search(r"^# (.+)$", text, re.M).group(1).strip()
    first = next(p for p in text.split("\n\n")
                 if p.strip() and not p.lstrip().startswith(("#", "[!", "<")))
    description = " ".join(first.split())
    return title, description, fix_links(body)


def main():
    """Write the page."""
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "site-root", "index.html")
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as readme:
        title, description, body = render(readme.read())
    light = HtmlFormatter(style="default").get_style_defs(".highlight")
    dark = HtmlFormatter(style="github-dark").get_style_defs(".highlight")
    dark = dark.replace(".highlight { background: #0d1117; }", ".highlight { background: none; }")
    page = PAGE.format(title=title, description=description.replace('"', "&quot;"), body=body,
                       site=SITE, repo=REPO, pygments_light=light, pygments_dark=dark)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as page_file:
        page_file.write(page)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
