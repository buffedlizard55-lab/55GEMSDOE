#!/usr/bin/env python3
"""Regenerate the compact HTML mirrors of the narrative docs from their Markdown.

The site's secondary pages (results, irregularities, sources, hypotheses) exist as
both ``.md`` (source of truth) and compact one-line ``.html`` (published mirror).
This script rebuilds the HTML mirrors from the Markdown so the two can never
drift.  Only the constructs used by these pages are supported: headings,
paragraphs, lists, tables, fenced code blocks, inline code, bold, links, quotes.

Usage:  python scripts/md_pages.py            # rebuild all mirrored pages
        python scripts/md_pages.py results    # rebuild one page
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

PAGES = {
    "results": "Results and evidence status",
    "irregularities": "Irregularity log",
    "sources": "Sources, evidence classes, and retrieval status",
    "hypotheses": "Ranked geological hypotheses",
}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(s: str) -> str:
    s = esc(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def convert(md: str) -> str:
    out: list[str] = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            lang = line[3:].strip()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append(f"<pre>{esc(chr(10).join(buf))}</pre>")
        elif line.startswith("### "):
            out.append(f"<h3>{inline(line[4:])}</h3>")
            i += 1
        elif line.startswith("## "):
            out.append(f"<h2>{inline(line[3:])}</h2>")
            i += 1
        elif line.startswith("# "):
            out.append(f"<h1>{inline(line[2:])}</h1>")
            i += 1
        elif line.startswith("> "):
            buf = [line[2:]]
            i += 1
            while i < len(lines) and lines[i].startswith("> "):
                buf.append(lines[i][2:])
                i += 1
            out.append(f"<blockquote>{inline(' '.join(buf))}</blockquote>")
        elif line.startswith("| ") and i + 1 < len(lines) and set(lines[i + 1].replace("|", "").replace("-", "").strip()) <= {" ", "-", ":"} and "-" in lines[i + 1]:
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].startswith("| "):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append("<table><tr>" + "".join(f"<th>{inline(c)}</th>" for c in header) + "</tr>")
            for r in rows:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            out.append("</table>")
        elif line.startswith("- "):
            buf = [line[2:]]
            i += 1
            while i < len(lines) and (lines[i].startswith("- ")
                                      or (lines[i].startswith("  ") and lines[i].strip())):
                if lines[i].startswith("- "):
                    buf.append(lines[i][2:])
                else:
                    buf[-1] = buf[-1] + " " + lines[i].strip()
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(b)}</li>" for b in buf) + "</ul>")
        elif re.match(r"^\d+\.\s", line):
            buf = [re.sub(r"^\d+\.\s", "", line)]
            i += 1
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i]):
                buf.append(re.sub(r"^\d+\.\s", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(b)}</li>" for b in buf) + "</ol>")
        elif line.strip() == "" or line.strip() == "<!-- E1-2026-10-09 -->":
            i += 1
        elif line.strip() == "---":
            out.append("<hr>")
            i += 1
        else:
            buf = [line]
            i += 1
            while (i < len(lines) and lines[i].strip() != "" and not lines[i].startswith(("#", "|", "- ", "> ", "```"))
                   and not re.match(r"^\d+\.\s", lines[i])):
                buf.append(lines[i])
                i += 1
            out.append(f"<p>{inline(' '.join(b.strip() for b in buf))}</p>")
    return "".join(out)


def build(slug: str) -> None:
    md = (DOCS / f"{slug}.md").read_text()
    title = PAGES[slug]
    html = (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f'<title>{esc(title)} · 55GEMSDOE</title><link rel="stylesheet" href="site.css"></head>\n'
        '<body><main><p><a href="index.html">← Executive summary</a></p>\n'
        + convert(md)
        + "\n</main></body></html>\n"
    )
    (DOCS / f"{slug}.html").write_text(html)
    print(f"wrote docs/{slug}.html ({len(html)} bytes)")


def main() -> None:
    args = sys.argv[1:]
    slugs = args if args else list(PAGES)
    for slug in slugs:
        build(slug)


if __name__ == "__main__":
    main()
