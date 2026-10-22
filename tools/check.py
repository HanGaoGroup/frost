"""Pre-deploy check: every page exists, every local link/image resolves, every page is noindex.

Usage: python3 tools/check.py   (exit code 1 on any problem; the deploy workflow stops)
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED = ["index.html", "datasets.html", "record-s1223.html", "benchmarks.html", "ai.html",
            "software.html", "publications.html", "team.html", "access.html", "404.html"]


def main():
    os.chdir(ROOT)
    problems = [f"missing page: {p}" for p in REQUIRED if not os.path.exists(p)]
    pages = glob.glob("*.html") + glob.glob("datasets/*.html")
    if len(glob.glob("datasets/*.html")) < 20:
        problems.append("too few dataset pages")
    n = 0
    for f in pages:
        s = open(f, encoding="utf-8").read()
        base = os.path.dirname(f)
        if 'name="robots" content="noindex' not in s:
            problems.append(f"{f}: missing noindex")
        if "{R}" in s:
            problems.append(f"{f}: unreplaced {{R}}")
        refs = re.findall(r'(?:href|src|data-full|data-zoom)="([^"]+)"', s)
        refs += re.findall(r"url\(([^)#%][^)]*)\)", s)
        for u in refs:
            if u.startswith(("http", "mailto:", "data:", "#")):
                continue
            u = u.split("#")[0].split("?")[0]
            n += 1
            if u and not os.path.exists(os.path.normpath(os.path.join(base, u))):
                problems.append(f"{f}: broken link {u}")
    print(f"checked {len(pages)} pages, {n} local references")
    for p in problems:
        print("PROBLEM:", p)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
