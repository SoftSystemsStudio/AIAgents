#!/usr/bin/env python3
"""Lightweight smoke check for the built static site.

This script is intentionally dependency-free so CI can run it
without installing the full application stack.
"""
import sys
from pathlib import Path


def main() -> int:
    p = Path("build/index.html")
    if not p.exists():
        print("ERROR: build/index.html not found. Run `bash build.sh` first.")
        return 2
    html = p.read_text(encoding="utf-8")
    ok_title = "Automation, Engineered" in html
    ok_cta = "/api/v1/auth/signup" in html or "Contact the Studio" in html
    if ok_title and ok_cta:
        print("OK: smoke check passed")
        return 0
    print("ERROR: smoke check failed")
    if not ok_title:
        print(" - expected hero title 'Automation, Engineered' not found")
    if not ok_cta:
        print(" - expected CTA '/api/v1/auth/signup' or 'Contact the Studio' not found")
    return 3


if __name__ == "__main__":
    sys.exit(main())
