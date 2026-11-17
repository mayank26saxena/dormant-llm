"""Copy the blog post in docs/blog into the personal site repo, ready to publish under /blog/<slug>/.

Usage:
  uv run --no-project --with matplotlib python -I scripts/publish_blog.py SITE_REPO SLUG --date 2026-11-17

What it does (nothing else in SITE_REPO is touched):
  - checks that SITE_REPO/blog/assets/{tokens.css,charts.js} are byte-identical to docs/blog/assets/ (the shared house style is
    owned by the first post's publish script; this script never overwrites it, so publishing here cannot change other posts);
  - writes SITE_REPO/blog/SLUG/index.html from docs/blog/index.html with asset paths pointed at ../assets/, content-hash
    cache-busting versions, canonical and link-preview (Open Graph / Twitter card) tags;
  - copies post.js and the two data files the page loads (data/figures.js, data/examples.js; never the .json files);
  - draws a 1200x630 share image at SITE_REPO/blog/SLUG/share.png (needs matplotlib);
  - records the post in SITE_REPO/blog/posts.json and regenerates the list page SITE_REPO/blog/index.html.
It never commits or pushes; review the result in the site repo first.
"""
import argparse
import hashlib
import html
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs/blog"
BASE = "https://mayank26saxena.github.io"
AUTHOR = "Mayank Saxena"
SPLIT = ("#4a524e", "#d09017")  # this post's split rule: score | checks


def h8(p):
    return hashlib.sha1(Path(p).read_bytes()).hexdigest()[:8]


def card(path, kicker, title, standfirst):
    """1200x630 share image in the house style (stone page, ink title, split rule)."""
    import textwrap

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    plt.rcParams["font.family"] = ["Helvetica Neue", "Arial", "DejaVu Sans"]
    fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor="#f2f3f3")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1200)
    ax.set_ylim(0, 630)
    ax.axis("off")
    ax.text(72, 548, kicker.upper(), fontsize=15, fontweight="bold", color="#2f6b57", va="center")
    lines = textwrap.wrap(title, 24)
    for i, ln in enumerate(lines[:3]):
        ax.text(72, 462 - i * 74, ln, fontsize=46, fontweight="bold", color="#0f172a", va="center")
    y_rule = 462 - len(lines[:3]) * 74 + 6
    ax.add_patch(Rectangle((72, y_rule), 60, 7, color=SPLIT[0]))
    ax.add_patch(Rectangle((132, y_rule), 60, 7, color=SPLIT[1]))
    sub = textwrap.fill(standfirst, 70)
    ax.text(72, y_rule - 50, sub, fontsize=17, color="#475569", va="top", linespacing=1.45)
    ax.text(72, 52, f"{AUTHOR}  ·  mayank26saxena.github.io", fontsize=15, color="#64748b", va="center")
    fig.savefig(path, dpi=100, facecolor="#f2f3f3")
    plt.close(fig)


def head_tags(url, title, desc, iso):
    e = lambda s: html.escape(s, quote=True)
    img = f"{url}share.png"
    return "\n".join([
        f'<link rel="canonical" href="{url}">',
        '<meta property="og:type" content="article">',
        f'<meta property="og:title" content="{e(title)}">',
        f'<meta property="og:description" content="{e(desc)}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{img}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="article:author" content="{AUTHOR}">',
        f'<meta property="article:published_time" content="{iso}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{e(title)}">',
        f'<meta name="twitter:description" content="{e(desc)}">',
        f'<meta name="twitter:image" content="{img}">',
    ])


def list_page(site, posts, fonts_link):
    """Same output as the first post's publish script, so either script can regenerate /blog/."""
    items = []
    for p in sorted(posts, key=lambda q: q["date"], reverse=True):
        d = date.fromisoformat(p["date"]).strftime("%-d %b %Y")
        items.append(f'<li><a href="{p["slug"]}/"><span class="pl-date">{d}</span><span class="pl-title">{html.escape(p["title"])}</span>'
                     f'<span class="pl-desc">{html.escape(p["description"])}</span></a></li>')
    css_v = h8(site / "blog/assets/tokens.css")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Blog · {AUTHOR}</title>
<meta name="description" content="Research notes on language models, safety and interpretability by {AUTHOR}.">
<link rel="canonical" href="{BASE}/blog/">
{fonts_link}
<link rel="stylesheet" href="assets/tokens.css?v={css_v}">
<style>
  .post-list {{ list-style: none; padding: 0; margin: 0 0 40px; }}
  .post-list li {{ border-top: 1px solid var(--rule); margin: 0; }}
  .post-list li:last-child {{ border-bottom: 1px solid var(--rule); }}
  .post-list a {{ display: block; padding: 22px 0; color: inherit; text-decoration: none; }}
  .pl-date {{ display: block; font: 500 12px var(--mono); color: var(--muted); margin-bottom: 6px; }}
  .pl-title {{ display: block; font: 600 24px/1.2 var(--display); letter-spacing: -.02em; margin-bottom: 6px; }}
  .pl-desc {{ display: block; font: 15px/1.5 var(--sans); color: var(--ink-2); }}
  .post-list a:hover .pl-title {{ color: var(--brand); }}
  .home-link {{ font: 500 13px var(--sans); color: var(--muted); text-decoration: none; }}
  .home-link:hover {{ color: var(--brand); }}
</style>
</head>
<body>
<header class="top"><div class="col">
  <p class="kicker"><a class="home-link" href="/">← {AUTHOR}</a></p>
  <h1>Blog</h1>
  <p class="standfirst">Research notes on language models, safety and interpretability.</p>
</div></header>
<main><div class="col">
<ul class="post-list">
{chr(10).join(items)}
</ul>
</div></main>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site")
    ap.add_argument("slug")
    ap.add_argument("--date", required=True, help="publication date, YYYY-MM-DD")
    a = ap.parse_args()
    site = Path(a.site).expanduser().resolve()
    assert (site / "index.html").exists(), "SITE_REPO does not look like the site repo"
    date.fromisoformat(a.date)
    blog, post = site / "blog", site / "blog" / a.slug
    for f in ("tokens.css", "charts.js"):
        if not (blog / "assets" / f).exists() or h8(blog / "assets" / f) != h8(SRC / "assets" / f):
            sys.exit(f"blog/assets/{f} in the site differs from docs/blog/assets/{f}: refresh the local copy from the site "
                     "(the shared style is owned by the first post), re-check this page, then publish again.")
    (post / "data").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC / "post.js", post / "post.js")
    for f in ("figures.js", "examples.js"):
        shutil.copyfile(SRC / "data" / f, post / "data" / f)

    t = (SRC / "index.html").read_text(encoding="utf-8")
    title = html.unescape(re.search(r"<title>(.*?)</title>", t, re.S).group(1)).strip()
    desc = html.unescape(re.search(r'<meta name="description" content="(.*?)">', t, re.S).group(1)).strip()
    h1 = re.sub(r"<[^>]+>", "", re.search(r"<h1>(.*?)</h1>", t, re.S).group(1)).strip()
    kicker = re.sub(r"<[^>]+>", "", re.search(r'<p class="kicker">(.*?)</p>', t, re.S).group(1)).strip()
    t = t.replace('href="assets/', 'href="../assets/').replace('src="assets/', 'src="../assets/')
    for rel, p in (("../assets/tokens.css", blog / "assets/tokens.css"), ("../assets/charts.js", blog / "assets/charts.js"),
                   ("post.js", post / "post.js"), ("data/figures.js", post / "data/figures.js"), ("data/examples.js", post / "data/examples.js")):
        t, n = re.subn(r'(?<=["/])' + re.escape(rel) + r"\?v=\w+", f"{rel}?v={h8(p)}", t)
        assert n == 1, f"{rel}: expected one versioned reference, found {n}"
    url = f"{BASE}/blog/{a.slug}/"
    t = re.sub(r'(<meta name="description" content=".*?">)', lambda m: m.group(1) + "\n" + head_tags(url, title, desc, a.date), t, count=1, flags=re.S)
    (post / "index.html").write_text(t, encoding="utf-8")
    card(post / "share.png", kicker, h1, desc.split(". ")[0] + ".")

    manifest = blog / "posts.json"
    posts = json.loads(manifest.read_text()) if manifest.exists() else []
    posts = [p for p in posts if p["slug"] != a.slug] + [dict(slug=a.slug, title=h1, description=desc, date=a.date)]
    manifest.write_text(json.dumps(posts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    fonts = re.search(r'<link href="https://fonts\.googleapis\.com/[^>]*>', t).group(0)
    # keep the list page's font link stable across posts: reuse the one it already has, if any
    old = (blog / "index.html").read_text(encoding="utf-8") if (blog / "index.html").exists() else ""
    m = re.search(r'<link href="https://fonts\.googleapis\.com/[^>]*>', old)
    (blog / "index.html").write_text(list_page(site, posts, m.group(0) if m else fonts), encoding="utf-8")
    print(f"published {a.slug}: {post / 'index.html'}")
    print(f"list page: {blog / 'index.html'} ({len(posts)} post{'s' if len(posts) != 1 else ''})")


if __name__ == "__main__":
    main()
