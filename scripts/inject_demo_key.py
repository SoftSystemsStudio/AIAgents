#!/usr/bin/env python3
"""Replace or insert the `meta[name="demo-key"]` tag in `index.html`.

Usage:
  # Use positional arg
  python3 scripts/inject_demo_key.py <DEMO_KEY> [path/to/index.html]

  # Or rely on env var
  DEMO_KEY=secret python3 scripts/inject_demo_key.py

The script is idempotent: it replaces an existing value or inserts the tag into <head>.
"""
import os
import sys
import re
from pathlib import Path


def inject_demo_key_into_html(key: str, index_path: Path) -> bool:
    if not index_path.exists():
        print(f"index.html not found at {index_path}")
        return False

    txt = index_path.read_text(encoding='utf-8')

    # Pattern to match existing meta tag
    pattern = re.compile(r'(<meta\s+name=(?:"|\')demo-key(?:"|\')\s+content=")[^\"]*("\s*/?>)', re.IGNORECASE)

    if pattern.search(txt):
        txt = pattern.sub(lambda m: m.group(1) + key + m.group(2), txt)
        index_path.write_text(txt, encoding='utf-8')
        print(f"Replaced existing demo-key in {index_path}")
        return True

    # Insert into <head> if present
    head_re = re.compile(r'<head[^>]*>', re.IGNORECASE)
    m = head_re.search(txt)
    if m:
        insert_at = m.end()
        txt = txt[:insert_at] + '\n    <meta name="demo-key" content="' + key + '">' + txt[insert_at:]
        index_path.write_text(txt, encoding='utf-8')
        print(f"Inserted demo-key meta into {index_path}")
        return True

    print('<head> tag not found; cannot inject demo-key')
    return False


def main(argv):
    key = None
    if len(argv) > 1 and argv[1].strip():
        key = argv[1].strip()
    else:
        key = os.environ.get('DEMO_KEY')

    if not key:
        print('No DEMO_KEY provided; nothing to do.')
        return 0

    index_path = Path(argv[2]) if len(argv) > 2 else Path('index.html')
    return 0 if inject_demo_key_into_html(key, index_path) else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
