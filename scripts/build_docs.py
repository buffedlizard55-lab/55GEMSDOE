"""Render docs/*.md to docs/*.html (GitHub Pages does not render .md under /docs) and write the band dictionary."""
from pathlib import Path

import markdown
import rasterio

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:920px;margin:2rem auto;padding:0 1rem;line-height:1.55;color:#1d2330}}
table{{border-collapse:collapse;width:100%;font-size:.92rem}}td,th{{border:1px solid #d7dce5;padding:.35rem .5rem;vertical-align:top;text-align:left}}
code{{background:#f1f3f7;padding:.1rem .3rem;border-radius:4px}}a{{color:#0b5cad}}
</style></head><body><p><a href="index.html">← Overview</a></p>{body}</body></html>"""


def dictionary():
    """Band dictionary from the GeoTIFF band tags (requires data/ to be present; skipped otherwise)."""
    p = ROOT / "data" / "training_features.tif"
    if not p.exists():
        return None
    rows = ["| band | description (from tag) | category | short name |", "|---|---|---|---|"]
    with rasterio.open(p) as s:
        for i in range(1, s.count + 1):
            t = s.tags(i)
            rows.append(f"| {i} | {t.get('description','')} | {t.get('data_category','')} | `{s.descriptions[i-1]}` |")
    return "# Feature band dictionary\n\nGenerated from `data/training_features.tif` band tags by `scripts/build_docs.py`.\n\n" + "\n".join(rows) + "\n"


def main():
    d = dictionary()
    if d:
        (DOCS / "data_dictionary.md").write_text(d)
    for md in sorted(DOCS.glob("*.md")):
        body = markdown.markdown(md.read_text(), extensions=["tables", "fenced_code"])
        title = md.stem.replace("-", " ").replace("_", " ").capitalize()
        (DOCS / f"{md.stem}.html").write_text(PAGE.format(title=title, body=body))
        print("rendered", md.name)


if __name__ == "__main__":
    main()
