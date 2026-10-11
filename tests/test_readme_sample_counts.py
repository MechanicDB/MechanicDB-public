"""README sample counts must equal the committed root sample's CSV row counts."""
import csv
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")


def _rows(table):
    with open(ROOT / f"{table}.csv", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="|"))


def _measured():
    codes = _rows("dtc_codes")
    sae = sum(row["is_oem_specific"] == "0" for row in codes)
    return {
        "dtc_codes": len(codes), "diagnostic_fixes": len(_rows("diagnostic_fixes")),
        "replacement_parts": len(_rows("replacement_parts")), "dtc_fixes_joined": len(_rows("dtc_fixes_joined")),
        "sae": sae, "oem": len(codes) - sae,
    }


def test_sample_file_table_states_committed_row_counts():
    measured = _measured()
    found = dict(re.findall(r"^\| `(\w+)\.csv` / `\.parquet` \| ([\d,]+) \|", README, re.M))
    assert set(found) == {"dtc_codes", "diagnostic_fixes", "replacement_parts", "dtc_fixes_joined"}, found
    assert {table: int(n.replace(",", "")) for table, n in found.items()} == \
        {table: measured[table] for table in found}


def test_full_vs_sample_table_states_committed_sample_counts():
    measured = _measured()
    labels = {"DTC codes": "dtc_codes", "— SAE-standard (universal)": "sae",
              "— OEM manufacturer-specific": "oem", "Ranked repair procedures": "diagnostic_fixes",
              "Replacement-parts mappings": "replacement_parts"}
    for label, key in labels.items():
        match = re.search(rf"^\| {re.escape(label)} \| [^|]+ \| ([\d,]+) \|", README, re.M)
        assert match, f"README row '{label}' not found"
        assert int(match.group(1).replace(",", "")) == measured[key], (label, match.group(1), measured[key])
