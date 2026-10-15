import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
README = PROJECT_ROOT / "README.md"
CASE_BRIEF = PROJECT_ROOT / "docs" / "01-case-study-brief.md"
STAKEHOLDERS = PROJECT_ROOT / "docs" / "02-stakeholders-and-interview-guide.md"
DECISIONS = PROJECT_ROOT / "docs" / "03-assumptions-and-decisions.md"

REQUIRED_FILES = (README, CASE_BRIEF, STAKEHOLDERS, DECISIONS)
PUBLIC_URL = "https://github.com/QaHuy/smart-warehouse-inbound-exceptions"
PAGES_URL = "https://qahuy.github.io/smart-warehouse-inbound-exceptions/"
DEMO_URL = "https://smart-warehouse-inbound-exceptions.vercel.app/"
# The only external URLs the foundation files may contain: the repository, its own Pages site,
# and the hosted demo.
APPROVED_URL = re.compile(
    rf"(?:{re.escape(PUBLIC_URL)}|{re.escape(PAGES_URL)}[^\s)]*|{re.escape(DEMO_URL)})"
)
DISCLOSURE = (
    "Personal WMS/WCS portfolio case study using synthetic data. "
    "WCS behavior and device events are simulated."
)


def _combined_markdown() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in REQUIRED_FILES)


def test_required_foundation_files_exist():
    missing = [str(path.relative_to(PROJECT_ROOT)) for path in REQUIRED_FILES if not path.is_file()]
    assert not missing, f"Missing foundation files: {missing}"


def test_required_disclosure_appears_verbatim_in_readme_and_case_brief():
    assert DISCLOSURE in README.read_text(encoding="utf-8")
    assert DISCLOSURE in CASE_BRIEF.read_text(encoding="utf-8")


def test_business_need_definitions_are_complete_and_unique():
    text = _combined_markdown()
    definitions = re.findall(r"(?m)^- `(?P<id>BN-\d{2})`:", text)
    expected = [f"BN-{number:02d}" for number in range(1, 5)]
    assert sorted(definitions) == expected
    assert all(count == 1 for count in Counter(definitions).values())


def test_later_identifier_namespaces_are_reserved_once_without_requirements():
    text = _combined_markdown()
    reserved = (
        "FR-01..FR-10",
        "BR-01..BR-10",
        "NFR-01..NFR-05",
        "US-01..US-12",
        "UAT-01..UAT-14",
    )
    for namespace in reserved:
        assert text.count(f"`{namespace}`") == 1, namespace

    # Detailed IDs belong to Tasks 2 and 7. Range endpoints inside the
    # reservation notation are allowed, but no standalone definitions are.
    assert not re.search(r"(?m)^- `(FR|BR|NFR|US|UAT)-\d{2}`:", text)


def test_readme_has_delivery_legend_and_only_approved_urls():
    text = README.read_text(encoding="utf-8")
    for label in ("Implemented", "Simulated", "Designed only"):
        assert label in text
    assert f"Public URL: {PUBLIC_URL}" in text
    urls = re.findall(r"https?://[^\s)]+", text)
    assert urls.count(PUBLIC_URL) == 1
    unapproved = [url for url in urls if not APPROVED_URL.fullmatch(url)]
    assert not unapproved, unapproved


def test_readme_links_to_the_hosted_demo():
    text = README.read_text(encoding="utf-8")
    assert f"**[Live demo]({DEMO_URL})**" in text
    assert f"{PAGES_URL}demo/" not in text


def test_readme_links_directly_to_each_foundation_artifact():
    text = README.read_text(encoding="utf-8")
    expected_links = (
        "[Case study brief](docs/01-case-study-brief.md)",
        "[Stakeholders and interview guide](docs/02-stakeholders-and-interview-guide.md)",
        "[Assumptions and decisions](docs/03-assumptions-and-decisions.md)",
        "[Structure tests](tests/test_structure.py)",
    )
    for link in expected_links:
        assert link in text, link


def test_maintenance_recovery_question_is_neutral_and_separates_probe():
    text = STAKEHOLDERS.read_text(encoding="utf-8")
    assert "without creating an inventory decision outside your role" not in text
    main_question_and_probe = re.compile(
        r"(?m)^5\. \*\*\[Observed fact\]\*\* For the most recent recovery event, "
        r"what evidence confirmed the device or flow was ready to continue\?\n"
        r"   - \*\*Probe:\*\* Who, if anyone, determined whether inventory should be "
        r"updated, and what criteria or record supported that determination\?$"
    )
    assert main_question_and_probe.search(text)


def test_foundation_contains_no_private_or_local_material():
    text = APPROVED_URL.sub("", _combined_markdown())
    banned_patterns = (
        r"(?i)kakadata",
        r"(?i)kakaonline",
        r"(?i)github\.com",
        r"(?i)https?://",
        r"(?i)[A-Z]:\\Users\\",
        r"(?i)(api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]",
    )
    for pattern in banned_patterns:
        assert not re.search(pattern, text), pattern
