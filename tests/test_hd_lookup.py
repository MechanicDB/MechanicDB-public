"""Synthetic public consumer tests; no commercial corpus dependency."""
import importlib.util
from pathlib import Path

import pytest

path = Path(__file__).resolve().parents[1] / "scripts/lookup_heavyduty.py"
spec = importlib.util.spec_from_file_location("hd_lookup", path)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def synthetic():
    core = dict(j1939_faults=[dict(fault_id=1, spn=1, fmi=3, source_id="synthetic", controller="Synthetic", oem_make="Synthetic", oem_code="")],
                diagnostic_fixes=[dict(fix_id=1, fault_id=1, probability_rank=10), dict(fix_id=2, fault_id=1, probability_rank=12)], replacement_parts=[])
    tables = dict(hd_applicability_contexts=[dict(context_key=v, dimension_key="synthetic_dimension", value_key=v, context_label=f"Synthetic {v}") for v in ("first", "second")],
                  hd_fault_contexts=[dict(fault_id=1, context_key=v, source_id="synthetic", source_sha256="a"*64, source_pages="1,2") for v in ("first", "second")],
                  hd_fix_contexts=[dict(fix_id=1, fault_id=1, context_key="first"), dict(fix_id=2, fault_id=1, context_key="second")], hd_part_contexts=[])
    metadata = dict(data_release_id="synthetic", applicability_revision=helper.revision(tables))
    return core, tables, metadata


def test_unknown_does_not_select_and_known_preserves_rank():
    core, tables, metadata = synthetic()
    helper.validate_memberships(tables, core)
    result = helper.lookup(core, tables, metadata, fault_id=1)
    assert result["applicability_status"] == "configuration_required"
    assert result["fixes"] == result["parts"] == []
    result = helper.lookup(core, tables, metadata, fault_id=1, contexts=["second"])
    assert result["applicability_status"] == "matched"
    assert result["fixes"][0]["probability_rank"] == 12
    assert result["parts"] == []


@pytest.mark.parametrize("contexts", [["wrong"], ["first", "second"], ["first", "first"]])
def test_invalid_context_has_no_selected_guidance(contexts):
    core, tables, metadata = synthetic()
    result = helper.lookup(core, tables, metadata, fault_id=1, contexts=contexts)
    assert result["applicability_status"] == "invalid_context"
    assert result["fixes"] == result["parts"] == []


def test_legacy_and_ambiguous_states():
    core, tables, metadata = synthetic()
    assert helper.lookup(core, None, None, fault_id=1)["applicability_status"] == "metadata_unavailable"
    core["j1939_faults"].append(dict(core["j1939_faults"][0], fault_id=2))
    assert helper.lookup(core, tables, metadata, spn=1, fmi=3)["applicability_status"] == "ambiguous_fault"
    assert helper.lookup(core, tables, metadata, fault_id=2)["applicability_status"] == "not_assessed"


def test_malformed_relationships_fail():
    core, tables, _ = synthetic()
    tables["hd_fix_contexts"][0]["fault_id"] = 2
    with pytest.raises(ValueError):
        helper.validate_memberships(tables, core)
