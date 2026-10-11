import importlib.util
import pathlib
import sqlite3

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("generate_stats", ROOT / "scripts" / "generate_stats.py")
gs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gs)


def _stats(tmp_path):
    db = tmp_path / "m.sqlite"
    con = sqlite3.connect(db)
    con.executescript(open(ROOT / "tests" / "fixtures" / "stats_mini.sql", encoding="utf-8").read())
    con.close()
    return gs.compute(str(db))


def test_cost_and_labor_stats_skip_nulls(tmp_path):
    s = _stats(tmp_path)
    assert s["fixes_with_labor"] < s["fixes"] and s["fixes_with_cost"] < s["fixes"]
    assert sum(c for _, c, _ in s["labor_buckets"]) == s["fixes_with_labor"]
    assert sum(c for _, c, _ in s["cost_buckets"]) == s["fixes_with_cost"]


def test_unknown_values_do_not_drag_medians_or_extremes(tmp_path):
    s = _stats(tmp_path)
    # 5 of 6 fixes have a cost (one is the 0/0 none_required row), 5 of 6 have labor.
    assert (s["fixes"], s["fixes_with_cost"], s["fixes_with_labor"]) == (6, 5, 5)
    assert s["cost_max"] == 900 and s["cost_1000plus"] == 0
    assert s["labor_max"] == 2.5 and s["labor_median"] == 1.0
    assert all(v is not None for _, v, _ in s["costliest"])
    allg = s["cost_groups"][0]
    assert allg["fixes"] == 6 and allg["median_max"] == 80
    assert all(isinstance(g[1], (int, float)) for g in s["labor_by_difficulty"])


def test_page_builds_and_counts_only_fixes_with_an_estimate(tmp_path):
    s = _stats(tmp_path)
    html = gs.build_page(s, {})
    assert "5 fixes with a parts-cost value (estimate or recorded zero), by est_parts_cost_max_usd" in html
    assert "5 fixes with a labor estimate, by est_labor_hours" in html
    assert "5 of the 6 fixes carry a parts-cost estimate" in html
    assert "see parts_cost_status and labor_status" in html


def test_parts_per_fix_includes_the_zero_part_bucket(tmp_path):
    s = _stats(tmp_path)
    # fixes 2 and 4 have no part rows; 1, 5 and 6 have one; 3 has two
    assert s["fixes_without_parts"] == 2
    assert [(k, c) for k, c, _ in s["parts_per_fix"]] == [(0, 2), (1, 3), (2, 1)]
    assert sum(c for _, c, _ in s["parts_per_fix"]) == s["fixes"]
    assert "% with 0" in gs.build_page(s, {})
