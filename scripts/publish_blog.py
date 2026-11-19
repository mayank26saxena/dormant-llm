"""Publish this project's blog post with the site's shared publisher (mayank26saxena.github.io/bin/publish_post.py).

  python3 scripts/publish_blog.py SITE_REPO [--date YYYY-MM-DD] [--dry-run] [...]

The publishing logic lives once, in the site repo; this wrapper only says where this post's page is and its slug.
Any other options are passed through (see `uv run SITE_REPO/bin/publish_post.py --help`). It never commits or pushes.
"""
import subprocess
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "docs/blog"
SLUG = "dormant-llm-backdoor-search"

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        sys.exit(__doc__)
    site = Path(sys.argv[1]).expanduser().resolve()
    sys.exit(subprocess.call(["uv", "run", "-q", str(site / "bin/publish_post.py"), str(SOURCE), "--slug", SLUG, *sys.argv[2:]]))
