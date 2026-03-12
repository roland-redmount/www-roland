#!/usr/bin/env python3
"""Build script for the static blog."""

import os
import re
import shutil

import mistune

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
ARTICLES_DIR = os.path.join(ROOT, "articles")
TEMPLATES_DIR = os.path.join(ROOT, "templates")


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


def collect_articles():
    articles = []
    for fname in os.listdir(ARTICLES_DIR):
        path = os.path.join(ARTICLES_DIR, fname)
        if fname.endswith(".html"):
            raw = read(path)
            slug = fname.replace(".html", "")
            content = raw
        elif fname.endswith(".md"):
            raw = read(path)
            slug = fname.replace(".md", "")
            content = mistune.html(raw)
        else:
            continue
        articles.append({
            "slug": slug,
            "filename": slug + ".html",
            "title": extract_meta(raw, "title") or slug,
            "date": extract_meta(raw, "date") or "9999-99-99",
            "content": content,
        })
    articles.sort(key=lambda a: a["date"], reverse=True)
    return articles


def build_sidebar(articles, root):
    lines = ['<aside class="sidebar">', "  <nav>", "    <h2>Posts</h2>", "    <ul>"]
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


def build_page(base, header, sidebar, content, title):
    page = base
    page = page.replace("{{header}}", header)
    page = page.replace("{{sidebar}}", sidebar)
    page = page.replace("{{content}}", content)
    page = page.replace("{{title}}", title)
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
        content = prefix_images(a["content"], root)
        page = build_page(base.replace("{{root}}", root), header, sidebar, content, a["title"])
        write(os.path.join(DIST, "articles", a["filename"]), page)

    # Build index (latest article)
    if articles:
        latest = articles[0]
        root = "./"
        sidebar = build_sidebar(articles, root)
        header = header_tpl.replace("{{root}}", root)
        content = prefix_images(latest["content"], root)
        page = build_page(base.replace("{{root}}", root), header, sidebar, content, latest["title"])
        write(os.path.join(DIST, "index.html"), page)

    # Copy styles
    shutil.copy2(os.path.join(ROOT, "styles.css"), os.path.join(DIST, "styles.css"))

    # Copy images
    images_src = os.path.join(ROOT, "images")
    if os.path.isdir(images_src):
        shutil.copytree(images_src, os.path.join(DIST, "images"))

    print(f"Built {len(articles)} article(s) -> dist/")


if __name__ == "__main__":
    main()
