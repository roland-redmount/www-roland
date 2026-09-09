#!/usr/bin/env python3
"""Build script for the static blog."""

import os
import re
import shutil
from datetime import date as date_type

import mistune

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
ARTICLES_HTML = os.path.join(ROOT, "articles")
ARTICLES_MD = os.path.join(ROOT, "www-vault")
TEMPLATES_DIR = os.path.join(ROOT, "templates")
ATOM_DIR = os.path.join(ROOT, "atom")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def extract_meta(html, key):
    m = re.search(rf"<!--\s*{key}:\s*(.+?)\s*-->", html)
    return m.group(1) if m else ""


def strip_meta(text):
    """Remove <!-- key: value --> comment lines from content."""
    return re.sub(r"<!--\s*\w+:\s*.+?\s*-->\n?", "", text)


def list_files(directory, ext):
    """Return the names of files in directory ending with ext."""
    if not os.path.isdir(directory):
        return []
    return sorted(
        f for f in os.listdir(directory)
        if f.endswith(ext) and os.path.isfile(os.path.join(directory, f))
    )


def enable_atom_snippets(html):
    """Wrap a fenced atom code block in the element that runs it.

    A post writes a snippet as a code block tagged atom, so the post stays
    readable as markdown. The code block is kept inside the element, so a
    reader without javascript still sees the snippet as a code block.
    """
    return re.sub(
        r'<pre><code class="language-atom">.*?</code></pre>',
        lambda m: f"<atom-snippet>{m.group(0)}</atom-snippet>",
        html,
        flags=re.DOTALL,
    )


def atom_snippet_script(content, root):
    """The script that runs snippets, for a page that has one."""
    if "<atom-snippet>" not in content:
        return ""
    return f'<script type="module" src="{root}atom/atom-snippet.js"></script>'


def slugify(name):
    """Turn a file name into a URL-friendly slug."""
    return name.lower().replace(" ", "_")


def collect_articles():
    articles = []
    sources = (
        [(ARTICLES_HTML, f, ".html") for f in list_files(ARTICLES_HTML, ".html")]
        + [(ARTICLES_MD, f, ".md") for f in list_files(ARTICLES_MD, ".md")]
    )
    for directory, fname, ext in sources:
        path = os.path.join(directory, fname)
        raw = read(path)
        title = extract_meta(raw, "title")
        # A markdown file is a note or a draft until it is given a title, so
        # that the vault can hold work that is not meant to be published yet.
        if ext == ".md" and not title:
            continue
        slug = slugify(fname[: -len(ext)])
        content = strip_meta(raw) if ext == ".html" else mistune.html(strip_meta(raw))
        content = enable_atom_snippets(content)
        articles.append({
            "slug": slug,
            "filename": slug + ".html",
            "title": title or slug,
            "date": extract_meta(raw, "date") or "9999-99-99",
            "content": content,
        })
    articles.sort(key=lambda a: a["date"], reverse=True)
    return articles


def build_sidebar(articles, root):
    sidebar_tpl = read(os.path.join(TEMPLATES_DIR, "sidebar.html"))
    lines = [
        '<aside class="sidebar">',
        sidebar_tpl,
        "  <nav>",
        "    <h2>Posts</h2>",
        "    <ul>",
    ]
    for a in articles:
        lines.append(
            f'      <li><a href="{root}articles/{a["slug"]}.html">{a["title"]}</a>'
            f'<span class="post-date">{a["date"]}</span></li>'
        )
    lines += ["    </ul>", "  </nav>", "</aside>"]
    return "\n".join(lines)


def prefix_images(html, root):
    """Rewrite bare <img src="file"> to <img src="{root}images/file">."""
    return re.sub(
        r'(<img\s[^>]*src=")(?!https?://|/|\.\./)([^"]+)',
        rf'\1{root}images/\2',
        html,
    )


def article_header(title, date):
    """Generate the article title and date HTML."""
    try:
        d = date_type.fromisoformat(date)
        pretty = d.strftime("%B %-d, %Y")
    except ValueError:
        pretty = date
    return f'<h1>{title}</h1>\n<p class="date">{pretty}</p>\n'


def build_page(base, header, sidebar, content, title, root):
    page = base
    page = page.replace("{{header}}", header)
    page = page.replace("{{sidebar}}", sidebar)
    page = page.replace("{{content}}", content)
    page = page.replace("{{title}}", title)
    page = page.replace("{{scripts}}", atom_snippet_script(content, root))
    return page


def main():
    # Clean dist
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(os.path.join(DIST, "articles"), exist_ok=True)

    base = read(os.path.join(TEMPLATES_DIR, "base.html"))
    header_tpl = read(os.path.join(TEMPLATES_DIR, "header.html"))

    articles = collect_articles()

    # Build each article page
    for a in articles:
        root = "../"
        sidebar = build_sidebar(articles, root)
        header = header_tpl.replace("{{root}}", root)
        content = article_header(a["title"], a["date"]) + prefix_images(a["content"], root)
        page = build_page(base.replace("{{root}}", root), header, sidebar, content, a["title"], root)
        write(os.path.join(DIST, "articles", a["filename"]), page)

    # Build index (latest article)
    if articles:
        latest = articles[0]
        root = "./"
        sidebar = build_sidebar(articles, root)
        header = header_tpl.replace("{{root}}", root)
        content = article_header(latest["title"], latest["date"]) + prefix_images(latest["content"], root)
        page = build_page(base.replace("{{root}}", root), header, sidebar, content, latest["title"], root)
        write(os.path.join(DIST, "index.html"), page)

    # Copy styles
    shutil.copy2(os.path.join(ROOT, "styles.css"), os.path.join(DIST, "styles.css"))

    # Copy the atom web front end, which is built in the atom repository and
    # copied here by its web/publish.sh; see atom/VERSION for which build.
    if os.path.isdir(ATOM_DIR):
        shutil.copytree(ATOM_DIR, os.path.join(DIST, "atom"))

    # Copy images
    images_src = os.path.join(ROOT, "images")
    if os.path.isdir(images_src):
        shutil.copytree(images_src, os.path.join(DIST, "images"))

    print(f"Built {len(articles)} article(s) -> dist/")


if __name__ == "__main__":
    main()
