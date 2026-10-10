import re
from collections import Counter
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TASK1_BRIEF = PROJECT_ROOT / "docs" / "01-case-study-brief.md"
SRS = PROJECT_ROOT / "docs" / "04-srs-fsd-lite.md"
BACKLOG = PROJECT_ROOT / "docs" / "05-product-goal-and-backlog.md"
STORIES = PROJECT_ROOT / "docs" / "06-user-stories-and-acceptance-criteria.md"

TASK2_FILES = (SRS, BACKLOG, STORIES)
PRODUCT_GOAL = (
    "Enable warehouse staff to receive and put away a pallet with visible status "
    "and controlled exception recovery without updating inventory before verified completion."
)
EXPECTED_ORDER = [
    ("US-01", "Validation"),
    ("US-02", "Unique identity"),
    ("US-03", "Location selection"),
    ("US-04", "Movement task and state"),
    ("US-05", "WCS dispatch"),
    ("US-06", "Event processing"),
    ("US-07", "Idempotency"),
    ("US-08", "Inventory commit"),
    ("US-09", "Exception queue"),
    ("US-10", "Retry, escalation, and cancellation"),
    ("US-11", "Audit trail"),
    ("US-12", "Metrics"),
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _task2_text() -> str:
    return "\n".join(_read(path) for path in TASK2_FILES)


def _peer_blocks(text: str, prefix: str, level: int) -> dict[str, str]:
    heading = "#" * level
    matches = list(re.finditer(rf"(?m)^{heading} ({prefix}-\d{{2}}) — .+$", text))
    next_peer_or_parent = re.compile(rf"(?m)^#{{1,{level}}} .+$")
    blocks = {}
    for match in matches:
        next_heading = next_peer_or_parent.search(text, match.end() + 1)
        end = next_heading.start() if next_heading else len(text)
        blocks[match.group(1)] = text[match.start() : end]
    return blocks


def _story_blocks(text: str) -> dict[str, str]:
    return _peer_blocks(text, "US", 2)


def _assert_requirement_metadata(text: str, prefix: str, count: int) -> None:
    blocks = _peer_blocks(text, prefix, 3)
    assert len(blocks) == count
    for identifier, block in blocks.items():
        statement = re.search(r"(?m)^- \*\*Statement:\*\* (.+)$", block)
        assert statement and " SHALL " in statement.group(1), identifier
        for field in ("Source", "Linked BN", "Verification method", "Acceptance signal"):
            assert re.search(rf"(?m)^- \*\*{re.escape(field)}:\*\* .+", block), (
                identifier,
                field,
            )


def _assert_measurable_nfr_thresholds(text: str) -> None:
    blocks = _peer_blocks(text, "NFR", 3)
    assert len(blocks) == 5
    for identifier, block in blocks.items():
        threshold = re.search(r"(?m)^- \*\*PROPOSED threshold:\*\* (.+)$", block)
        assert threshold, identifier
        assert re.search(
            r"(?i)(\d|\bzero\b|\bone\b|\ball\b|\bnone\b|\btrue\b|\bfalse\b)",
            threshold.group(1),
        ), identifier


def _assert_all_ac_references_resolve(srs_text: str, backlog_text: str, stories_text: str) -> None:
    defined = re.findall(r"(?m)^### (AC-US-\d{2}-\d{2}) — .+$", stories_text)
    assert defined
    assert len(defined) == len(set(defined))
    referenced = set(
        re.findall(
            r"AC-US-\d{2}-\d{2}",
            "\n".join((srs_text, backlog_text, stories_text)),
        )
    )
    assert referenced <= set(defined), f"Undefined AC references: {sorted(referenced - set(defined))}"


def _assert_nfr_human_checkpoints(text: str) -> None:
    section = re.search(
        r"(?ms)^### NFR human review checkpoints\n.*?(?=^## Interfaces and data overview)",
        text,
    )
    assert section
    rows = re.findall(
        r"(?m)^\| `(NFR-\d{2})` \| (PROPOSED [^|]+?) \| ([^|]+?) \| ([^|]+?) \|$",
        section.group(0),
    )
    assert [identifier for identifier, _, _, _ in rows] == [
        f"NFR-{number:02d}" for number in range(1, 6)
    ]
    for identifier, role, checkpoint, trigger in rows:
        assert role.strip() and checkpoint.strip() and trigger.strip(), identifier


def _assert_device_offline_recovery_chain(stories_text: str) -> None:
    blocks = _story_blocks(stories_text)
    dispatch = blocks["US-05"]
    recovery = blocks["US-10"]
    assert re.search(r"offline[^\n]*`FAILED`[^\n]*active exception", dispatch, re.IGNORECASE)
    assert re.search(r"first failure[^\n]*not a retry", dispatch, re.IGNORECASE)
    assert re.search(r"device remains offline[^\n]*retry attempt one", recovery, re.IGNORECASE)
    assert re.search(r"retry attempt two[^\n]*FAILED", recovery, re.IGNORECASE)
    assert re.search(r"increments failure evidence[^\n]*actionable exception", recovery, re.IGNORECASE)
    assert re.search(
        r"initial failure plus two failed retries[^\n]*third failure[^\n]*escalat",
        recovery,
        re.IGNORECASE,
    )
    assert re.search(r"no third retry command", recovery, re.IGNORECASE)


def _definitions(text: str, prefix: str, level: int) -> list[str]:
    return re.findall(rf"(?m)^{'#' * level} ({prefix}-\d{{2}}) — .+$", text)


def test_required_task2_artifacts_exist():
    missing = [str(path.relative_to(PROJECT_ROOT)) for path in TASK2_FILES if not path.is_file()]
    assert not missing, f"Missing Task 2 artifacts: {missing}"


def test_definition_counts_ranges_and_uniqueness():
    task1_text = _read(TASK1_BRIEF)
    srs_text = _read(SRS)
    stories_text = _read(STORIES)

    expected = {
        "BN": [f"BN-{number:02d}" for number in range(1, 5)],
        "FR": [f"FR-{number:02d}" for number in range(1, 11)],
        "BR": [f"BR-{number:02d}" for number in range(1, 11)],
        "NFR": [f"NFR-{number:02d}" for number in range(1, 6)],
        "US": [f"US-{number:02d}" for number in range(1, 13)],
    }
    actual = {
        "BN": re.findall(r"(?m)^- `(BN-\d{2})`:", task1_text),
        "FR": _definitions(srs_text, "FR", 3),
        "BR": _definitions(srs_text, "BR", 3),
        "NFR": _definitions(srs_text, "NFR", 3),
        "US": _definitions(stories_text, "US", 2),
    }
    for namespace, identifiers in actual.items():
        assert identifiers == expected[namespace], namespace
        assert all(count == 1 for count in Counter(identifiers).values()), namespace


def test_srs_has_required_status_sections_and_atomic_requirement_metadata():
    text = _read(SRS)
    assert re.search(r"(?m)^# .+Draft.+Personal synthetic portfolio", text)
    required_sections = (
        "Version history",
        "Purpose",
        "Audience",
        "Scope",
        "System context",
        "Glossary",
        "Business needs",
        "Assumptions and constraints",
        "Functional requirements",
        "Business rules",
        "Non-functional requirements catalog",
        "Interfaces and data overview",
        "Error catalogue",
        "Traceability summary",
        "Verification methods",
        "Open questions",
        "Review findings",
    )
    for section in required_sections:
        assert f"## {section}" in text, section

    _assert_requirement_metadata(text, "FR", 10)
    _assert_requirement_metadata(text, "NFR", 5)


def test_every_fr_links_existing_bn_and_every_bn_is_covered():
    text = _read(SRS)
    valid_bn = {f"BN-{number:02d}" for number in range(1, 5)}
    coverage = Counter()
    for identifier in (f"FR-{number:02d}" for number in range(1, 11)):
        block = re.search(
            rf"(?ms)^### {identifier} — .*?(?=^### FR-\d{{2}} — |^## Business rules)",
            text,
        )
        assert block, identifier
        links = set(re.findall(r"BN-\d{2}", block.group(0)))
        assert links and links <= valid_bn, identifier
        coverage.update(links)
    assert set(coverage) == valid_bn


def test_exact_product_goal_and_ordered_backlog():
    backlog_text = _read(BACKLOG)
    story_text = _read(STORIES)
    assert backlog_text.count(PRODUCT_GOAL) == 1
    backlog_rows = re.findall(
        r"(?m)^\| (?P<rank>\d{1,2}) \| `(?P<id>US-\d{2})` \| (?P<title>[^|]+?) \|",
        backlog_text,
    )
    assert [(identifier, title) for _, identifier, title in backlog_rows] == EXPECTED_ORDER
    assert [int(rank) for rank, _, _ in backlog_rows] == list(range(1, 13))
    assert _definitions(story_text, "US", 2) == [identifier for identifier, _ in EXPECTED_ORDER]
    for identifier, title in EXPECTED_ORDER:
        assert re.search(rf"(?m)^## {identifier} — {re.escape(title)}$", story_text)


def test_each_story_has_metadata_invest_and_testable_acceptance_criteria():
    text = _read(STORIES)
    blocks = _story_blocks(text)
    assert list(blocks) == [f"US-{number:02d}" for number in range(1, 13)]
    all_ac_ids: list[str] = []
    valid_links = {
        "BN": {f"BN-{number:02d}" for number in range(1, 5)},
        "FR": {f"FR-{number:02d}" for number in range(1, 11)},
        "BR": {f"BR-{number:02d}" for number in range(1, 11)},
        "NFR": {f"NFR-{number:02d}" for number in range(1, 6)},
    }
    for story_id, block in blocks.items():
        for field in (
            "Persona",
            "Capability",
            "Business value",
            "Linked BN",
            "Linked FR",
            "Linked BR",
            "Linked NFR",
            "Assumptions",
            "Dependencies",
            "Priority status",
            "Estimate status",
            "INVEST check",
        ):
            assert re.search(rf"(?m)^- \*\*{re.escape(field)}:\*\* .+", block), (
                story_id,
                field,
            )
        for prefix, allowed in valid_links.items():
            line = re.search(rf"(?m)^- \*\*Linked {prefix}:\*\* (.+)$", block)
            links = set(re.findall(rf"{prefix}-\d{{2}}", line.group(1)))
            assert links and links <= allowed, (story_id, prefix)

        ac_matches = list(re.finditer(rf"(?m)^### (AC-{story_id}-\d{{2}}) — .+$", block))
        assert len(ac_matches) >= 2, story_id
        all_ac_ids.extend(match.group(1) for match in ac_matches)
        for index, match in enumerate(ac_matches):
            ac_block = block[
                match.start() : ac_matches[index + 1].start()
                if index + 1 < len(ac_matches)
                else len(block)
            ]
            assert re.search(r"(?m)^- \*\*Given\*\* .+", ac_block)
            assert re.search(r"(?m)^- \*\*When\*\* .+", ac_block)
            assert re.search(r"(?m)^- \*\*Then\*\* .+", ac_block)
        assert "Positive AC" in block
        assert re.search(r"Negative/boundary AC", block)

    assert len(all_ac_ids) == len(set(all_ac_ids))
    _assert_all_ac_references_resolve(_read(SRS), _read(BACKLOG), text)


def test_every_business_rule_has_story_and_verification_route():
    srs_text = _read(SRS)
    story_text = _read(STORIES)
    blocks = _peer_blocks(srs_text, "BR", 3)
    assert list(blocks) == [f"BR-{number:02d}" for number in range(1, 11)]
    for identifier, block in blocks.items():
        assert "**Verification route:**" in block, identifier
        assert re.search(rf"(?m)^- \*\*Linked BR:\*\* .*\b{identifier}\b", story_text), identifier


def test_nfr_catalog_has_proposed_measurable_controls():
    text = _read(SRS)
    blocks = _peer_blocks(text, "NFR", 3)
    assert list(blocks) == [f"NFR-{number:02d}" for number in range(1, 6)]
    for identifier, body in blocks.items():
        for field in (
            "PROPOSED threshold",
            "Test conditions",
            "Rationale",
            "Source",
            "Verification method",
        ):
            assert re.search(rf"(?m)^- \*\*{re.escape(field)}:\*\* .+", body), (
                identifier,
                field,
            )
    _assert_measurable_nfr_thresholds(text)


def test_all_nfrs_have_individual_proposed_human_checkpoints():
    _assert_nfr_human_checkpoints(_read(SRS))


def test_high_risk_story_behaviors_are_explicit():
    blocks = _story_blocks(_read(STORIES))
    assert re.search(r"duplicate[^\n]*event_id", blocks["US-07"], re.IGNORECASE)
    assert re.search(r"success[^\n]*duplicate", blocks["US-07"], re.IGNORECASE)
    assert re.search(r"no second (state or inventory mutation|inventory or state mutation)", blocks["US-07"], re.IGNORECASE)

    assert re.search(r"exactly one inventory movement", blocks["US-08"], re.IGNORECASE)
    assert re.search(r"no inventory movement[^\n]*before", blocks["US-08"], re.IGNORECASE)

    assert re.search(r"retry attempts? one and two[^\n]*allowed", blocks["US-10"], re.IGNORECASE)
    assert re.search(r"third failure[^\n]*escalat", blocks["US-10"], re.IGNORECASE)
    assert re.search(r"cancell?ation[^\n]*documented non-terminal states", blocks["US-10"], re.IGNORECASE)


def test_device_offline_recovery_chain_is_testable_end_to_end():
    _assert_device_offline_recovery_chain(_read(STORIES))


def test_mutation_missing_fr10_source_is_rejected():
    text = _read(SRS)
    blocks = _peer_blocks(text, "FR", 3)
    source = re.search(r"(?m)^- \*\*Source:\*\* .+\n", blocks["FR-10"])
    assert source
    mutated = text.replace(source.group(0), "", 1)
    with pytest.raises(AssertionError):
        _assert_requirement_metadata(mutated, "FR", 10)


def test_mutation_invalid_ac_reference_is_rejected():
    srs_text = _read(SRS)
    assert "AC-US-12-02" in srs_text
    mutated = srs_text.replace("AC-US-12-02", "AC-US-99-99", 1)
    with pytest.raises(AssertionError):
        _assert_all_ac_references_resolve(mutated, _read(BACKLOG), _read(STORIES))


def test_mutation_non_measurable_nfr_threshold_is_rejected():
    text = _read(SRS)
    mutated, count = re.subn(
        r"(?m)^- \*\*PROPOSED threshold:\*\* 30 of 30 consecutive clean-state runs produce identical normalized output\.$",
        "- **PROPOSED threshold:** Repeated clean-state runs produce identical normalized output.",
        text,
        count=1,
    )
    assert count == 1
    with pytest.raises(AssertionError):
        _assert_measurable_nfr_thresholds(mutated)


def test_task2_artifacts_have_no_banned_claims_or_private_material():
    text = _task2_text()
    banned_patterns = (
        r"(?i)\bTBD\b",
        r"(?i)\bapproved\b",
        r"(?i)\bbaselined\b",
        r"(?i)ISO[-/ ]?compliant",
        r"(?i)WCAG[-/ ]?compliant",
        r"(?i)kakadata",
        r"(?i)kakaonline",
        r"(?i)github\.com",
        r"(?i)https?://",
        r"(?i)[A-Z]:\\Users\\",
        r"(?i)(api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]",
        r"(?i)\b(measured savings|measured improvement|guaranteed benefit|ROI)\b",
        r"(?i)\b(story points?|person-days?|ideal days?)\s*[:=]\s*\d+",
    )
    for pattern in banned_patterns:
        assert not re.search(pattern, text), pattern
