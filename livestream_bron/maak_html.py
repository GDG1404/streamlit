"""Maakt HANDLEIDING.html uit HANDLEIDING.md (één bestand, met de beelden erin).

  python maak_html.py <pad naar livestream/>
"""
import base64
import os
import re
import sys

from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.tasklists import tasklists_plugin

ROOT = os.path.abspath(sys.argv[1])


def github_slug(value, separator="-"):
    """Zelfde ankers als op GitHub, zodat de inhoudstafel overal werkt."""
    value = re.sub(r"[^\w\- ]", "", value.strip().lower())
    return value.replace(" ", separator)


def embed_images(html):
    def repl(m):
        path = os.path.join(ROOT, m.group(1))
        with open(path, "rb") as fh:
            data = base64.b64encode(fh.read()).decode()
        return f'src="data:image/png;base64,{data}"'
    return re.sub(r'src="(beelden/[^"]+\.png)"', repl, html)


CSS = """
:root { --ink:#1b1b1a; --muted:#5d5c58; --line:#dddcd5; --accent:#2a78d6; --code:#f3f2ee; }
body { font-family: "Segoe UI", system-ui, -apple-system, sans-serif; color: var(--ink);
       max-width: 920px; margin: 0 auto; padding: 24px 20px 80px; line-height: 1.55;
       background: #fcfcfb; }
h1 { font-size: 2.1em; margin-bottom: 0.1em; }
h2 { border-bottom: 2px solid var(--line); padding-bottom: 0.25em; margin-top: 2.2em; }
h3 { margin-top: 1.6em; }
a { color: var(--accent); }
img { max-width: 100%; border: 1px solid var(--line); border-radius: 6px; }
table { border-collapse: collapse; width: 100%; margin: 0.8em 0; font-size: 0.95em; }
th, td { border: 1px solid var(--line); padding: 6px 9px; text-align: left; vertical-align: top; }
th { background: #f0efea; }
code { background: var(--code); padding: 1px 5px; border-radius: 4px; font-size: 0.92em; }
pre { background: var(--code); padding: 12px 14px; border-radius: 6px; overflow-x: auto; }
pre code { padding: 0; background: none; }
blockquote { margin: 1em 0; padding: 0.6em 1em; border-left: 4px solid var(--accent);
             background: #eef4fc; border-radius: 0 6px 6px 0; }
blockquote p { margin: 0.3em 0; }
li.task-list-item { list-style: none; margin-left: -1.3em; }
input.task-list-item-checkbox { margin-right: 0.5em; transform: scale(1.2); }
hr { border: none; border-top: 1px solid var(--line); margin: 2em 0; }
@media print {
  body { max-width: none; background: white; }
  h2 { page-break-before: always; }
  img, table, pre { page-break-inside: avoid; }
  a { color: inherit; text-decoration: none; }
}
"""


def main():
    with open(os.path.join(ROOT, "HANDLEIDING.md"), encoding="utf-8") as fh:
        text = fh.read()
    # CommonMark zoals op GitHub: ook codeblokken en lijstjes binnen een stap
    md = (MarkdownIt("commonmark").enable("table")
          .use(anchors_plugin, max_level=3, slug_func=github_slug)
          .use(tasklists_plugin, enabled=True))
    body = embed_images(md.render(text))
    html = ("<!doctype html>\n<html lang=\"nl\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            "<title>CanSat 2027 — Livestream: handleiding</title>\n"
            f"<style>{CSS}</style>\n</head>\n<body>\n{body}\n</body>\n</html>\n")
    out = os.path.join(ROOT, "HANDLEIDING.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    # controle: elke link in de inhoudstafel moet een anker hebben
    ids = set(re.findall(r'id="([^"]+)"', html))
    links = re.findall(r'href="#([^"]+)"', html)
    missing = [l for l in links if l not in ids]
    print(f"{out}: {len(html) // 1024} kB, {len(links)} interne links, ontbrekend: {missing}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
