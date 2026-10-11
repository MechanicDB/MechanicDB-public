"""Surfaces not covered by the private claims tests must state only current counts."""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SURFACES = ["assets/kaggle-cover.html", "notebooks/mechanicdb-starter.ipynb", "site.webmanifest"] + \
    sorted(str(p.relative_to(ROOT)).replace("\\", "/") for p in (ROOT / "stats" / "charts").glob("*.svg"))
NUMBER = re.compile(r"(?<![\d.,])(\d{1,3}(?:,\d{3})+)(?![\d,])")
# Dollar amounts and unspaced ranges ("$1,000 and above", "$250-1,500") are prices, not dataset counts.
# A spaced dash ("$149 - 56,561 ranked fixes") is prose, so the count after it is still checked.
MONEY = re.compile(r"\$[\d,]+(?:\.\d+)?(?:[–—-]\$?[\d,]+)?")


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


def _counts(text):
    return [m.group(1) for m in NUMBER.finditer(MONEY.sub(" ", text))]


def test_money_masking_hides_prices_but_not_counts():
    assert _counts("$149 — 56,561 ranked fixes") == ["56,561"]
    assert _counts("$149 - 56,561 ranked fixes") == ["56,561"]
    assert _counts("Professional Required · $250–1,500 · 2.0 h") == []
    assert _counts("$250-$1,500 and $1,000 and above") == []


def test_count_surfaces_state_only_current_counts():
    charts = sorted((ROOT / "stats" / "charts").glob("*.svg"))
    assert charts, "stats/charts has no SVGs; the surface list would silently shrink"
    allowed, stale = _allowed(), []
    for rel in SURFACES:
        for number in _counts((ROOT / rel).read_text(encoding="utf-8")):
            if int(number.replace(",", "")) not in allowed:
                stale.append(f"{rel}: {number}")
    assert not stale, stale[:20]
