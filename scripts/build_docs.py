"""Render docs/*.md that have no HTML twin yet (existing governed HTML pages are never overwritten).

Also writes the feature band dictionary from the GeoTIFF band tags when data/ is present.
"""
from pathlib import Path

import markdown
import rasterio

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><link rel="stylesheet" href="site.css"></head><body><p><a href="index.html">&larr; Overview</a></p>{body}</body></html>"""


def dictionary():
    p = ROOT / "data" / ("gems-geodawn-numerical-features.tif" if (ROOT / "data" / "gems-geodawn-numerical-features.tif").exists() else "training_features.tif")  # IR-55-026
    if not p.exists():
        return None
    rows = ["| band | description (from tag) | category | short name |", "|---|---|---|---|"]
    with rasterio.open(p) as s:
        for i in range(1, s.count + 1):
            t = s.tags(i)
            rows.append(f"| {i} | {t.get('description', '')} | {t.get('data_category', '')} | `{s.descriptions[i-1]}` |")
    return ("# Feature band dictionary\n\nGenerated from `data/training_features.tif` band tags by "
            "`scripts/build_docs.py`.\n\n" + "\n".join(rows) + "\n")


def main():
    d = dictionary()
    if d:
        (DOCS / "data_dictionary.md").write_text(d)
    for md in sorted(DOCS.glob("*.md")):
        html = DOCS / f"{md.stem}.html"
        if html.exists():
            continue
        body = markdown.markdown(md.read_text(), extensions=["tables", "fenced_code"])
        title = md.stem.replace("-", " ").replace("_", " ").capitalize()
        html.write_text(PAGE.format(title=title, body=body))
        print("rendered", md.name)


if __name__ == "__main__":
    main()
