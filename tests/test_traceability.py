import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS = PROJECT_ROOT / "docs"


def _text(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def _ids(prefix: str, start: int, end: int) -> set[str]:
    return {f"{prefix}-{index:02d}" for index in range(start, end + 1)}


def test_handover_documents_exist():
    for name in (
        "07-requirements-traceability-matrix.md",
        "08-uat-pack-and-results.md",
        "09-defect-and-change-log.md",
        "10-user-guide-and-demo-script.md",
    ):
        assert (DOCS / name).is_file(), name


def test_rtm_covers_every_reserved_requirement_story_and_uat_id():
    text = _text("07-requirements-traceability-matrix.md")
    for prefix, start, end in (("BN", 1, 4), ("FR", 1, 10), ("BR", 1, 10), ("US", 1, 12), ("UAT", 1, 14)):
        found = set(re.findall(rf"\b{prefix}-\d{{2}}\b", text))
        assert _ids(prefix, start, end) <= found, (prefix, sorted(_ids(prefix, start, end) - found))
    assert "0 orphaned requirements" in text
    assert "14 PASS" in text


def test_uat_pack_records_fourteen_passed_cases_with_actual_results_and_evidence():
    text = _text("08-uat-pack-and-results.md")
    rows = {
        match.group("id"): match.group(0)
        for match in re.finditer(r"(?m)^\| (?P<id>UAT-\d{2}) \|.*$", text)
    }
    assert set(rows) == _ids("UAT", 1, 14)
    for case_id, row in rows.items():
        assert "| PASS |" in row, case_id
        assert "tests/uat.test.mjs" in row, case_id
        columns = [column.strip() for column in row.strip("|").split("|")]
        assert len(columns) == 8, (case_id, columns)
        assert columns[6] and columns[6] != "—", case_id
    assert "14 / 14 passed" in text


def test_defect_log_is_honest_and_change_control_is_explicit():
    text = _text("09-defect-and-change-log.md")
    assert "Open defects at handover: **0**" in text
    assert "No production deployment" in text
    assert "Change request" in text
    for classification in ("Defect", "Change request", "Assumption gap"):
        assert classification in text


def test_demo_script_is_timed_recruiter_ready_and_discloses_simulation():
    text = _text("10-user-guide-and-demo-script.md")
    assert "5-minute recruiter walkthrough" in text
    assert "Personal WMS/WCS portfolio case study using synthetic data." in text
    assert "WCS behavior and device events are simulated." in text
    for scenario in ("Happy path", "Offline escalation", "Duplicate event"):
        assert scenario in text
    assert "python -m http.server 8765" in text


def test_evidence_screenshots_exist_and_are_nontrivial():
    assets = PROJECT_ROOT / "assets"
    for name in (
        "01-inbound-workbench.png",
        "02-happy-path-inventory.png",
        "03-offline-escalation.png",
        "04-duplicate-event.png",
    ):
        path = assets / name
        assert path.is_file(), name
        assert path.stat().st_size > 50_000, name
