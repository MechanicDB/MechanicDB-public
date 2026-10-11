"""Surfaces not covered by the private claims tests must state only current counts."""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SURFACES = ["assets/kaggle-cover.html", "notebooks/mechanicdb-starter.ipynb", "site.webmanifest"] + \
    sorted(str(p.relative_to(ROOT)).replace("\\", "/") for p in (ROOT / "stats" / "charts").glob("*.svg"))
NUMBER = re.compile(r"(?<![\d.,])(\d{1,3}(?:,\d{3})+)(?![\d,])")
# Dollar amounts and ranges ("$1,000 and above", "$250-1,500") are prices, not dataset counts.
MONEY = re.compile(r"\$[\d,]+(?:\s*[–—-]\s*[\d,]+)?")


def _allowed():
    claims = json.loads((ROOT / "claims.json").read_text(encoding="utf-8"))
    values = set()
    for tier in ("standard", "oem", "heavyduty"):
        values |= {v for v in claims[tier].values() if isinstance(v, int) and not isinstance(v, bool)}
    values.add(claims["oem"]["codes"] - claims["standard"]["codes"])  # OEM-specific codes
    def walk(x):
        if isinstance(x, bool):
            return
        if isinstance(x, int):
            values.add(x)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(json.loads((ROOT / "stats" / "data.json").read_text(encoding="utf-8")))
    return values


def test_count_surfaces_state_only_current_counts():
    allowed, stale = _allowed(), []
    for rel in SURFACES:
        text = MONEY.sub(" ", (ROOT / rel).read_text(encoding="utf-8"))
        for match in NUMBER.finditer(text):
            if int(match.group(1).replace(",", "")) not in allowed:
                stale.append(f"{rel}: {match.group(1)}")
    assert not stale, stale[:20]
