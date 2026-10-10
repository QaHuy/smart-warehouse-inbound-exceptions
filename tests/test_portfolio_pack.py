import re
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DELIVERABLES = PROJECT_ROOT / "deliverables"
SITE_INDEX = PROJECT_ROOT / "site" / "index.html"
CONTENT = PROJECT_ROOT / "tools" / "portfolio" / "content.mjs"
README = PROJECT_ROOT / "README.md"
DISCLOSURE = (
    "Personal WMS/WCS portfolio case study using synthetic data. "
    "WCS behavior and device events are simulated."
)
PACK = (
    "Smart-Warehouse-BA-Case-Study.pdf",
    "Smart-Warehouse-BA-Case-Study.docx",
    "Smart-Warehouse-BA-One-Pager.pdf",
)
PRIVATE_PATTERNS = (
    r"(?i)kakadata",
    r"(?i)kakaonline",
    r"(?i)[A-Z]:\\Users\\",
    r"(?i)file:///",
    r"(?i)(api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]",
)


def test_recruiter_pack_files_exist_and_readme_links_resolve():
    for name in PACK:
        path = DELIVERABLES / name
        assert path.is_file(), name
        assert path.stat().st_size > 50_000, name
    readme = README.read_text(encoding="utf-8")
    for target in re.findall(r"\]\(((?:deliverables|assets|docs|data|api|diagrams|tools)/[^)]*)\)", readme):
        assert (PROJECT_ROOT / target).exists(), target


def test_one_pager_is_a_single_page():
    pdf = (DELIVERABLES / "Smart-Warehouse-BA-One-Pager.pdf").read_bytes().decode("latin-1")
    assert len(re.findall(r"/Type\s*/Page(?!s)", pdf)) == 1


def test_web_and_word_case_study_keep_the_disclosure():
    assert DISCLOSURE in SITE_INDEX.read_text(encoding="utf-8")
    with zipfile.ZipFile(DELIVERABLES / "Smart-Warehouse-BA-Case-Study.docx") as docx:
        body = re.sub(r"<[^>]+>", "", docx.read("word/document.xml").decode("utf-8"))
    assert DISCLOSURE in body


def test_recruiter_pack_sources_contain_no_private_or_local_material():
    with zipfile.ZipFile(DELIVERABLES / "Smart-Warehouse-BA-Case-Study.docx") as docx:
        docx_text = docx.read("word/document.xml").decode("utf-8")
    for text in (SITE_INDEX.read_text(encoding="utf-8"), CONTENT.read_text(encoding="utf-8"), docx_text):
        for pattern in PRIVATE_PATTERNS:
            assert re.search(pattern, text) is None, pattern
