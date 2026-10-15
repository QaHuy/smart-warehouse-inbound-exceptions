import re
from html.parser import HTMLParser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = PROJECT_ROOT / "prototype"
HTML = PROTOTYPE / "index.html"
CSS = PROTOTYPE / "styles.css"
APP = PROTOTYPE / "app.js"
REPO_URL = "https://github.com/QaHuy/smart-warehouse-inbound-exceptions"
DEMO_URL = "https://smart-warehouse-inbound-exceptions.vercel.app/"
# The only external URLs the prototype may mention: its source repository and its hosted demo.
APPROVED_URL = re.compile(rf"(?:{re.escape(REPO_URL)}|{re.escape(DEMO_URL)}[^\s\"'<>]*)")


class PrototypeParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def _parse():
    parser = PrototypeParser()
    parser.feed(HTML.read_text(encoding="utf-8"))
    return parser.tags


def test_static_prototype_files_exist_and_use_local_assets_only():
    for path in (HTML, CSS, APP):
        assert path.is_file(), path
    html = HTML.read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")
    urls = re.findall(r"https?://[^\s\"'<>]+", html)
    assert all(APPROVED_URL.fullmatch(url) for url in urls), urls
    loaded = [
        attrs.get("src") or attrs.get("href")
        for tag, attrs in _parse()
        if tag in {"script", "img"} or (tag == "link" and attrs.get("rel") in {"stylesheet", "icon"})
    ]
    assert loaded and all(ref and ref.startswith("./") for ref in loaded), loaded
    assert not re.search(r"\b(fetch|XMLHttpRequest|WebSocket)\s*\(", app)
    assert '<link rel="stylesheet" href="./styles.css">' in html
    assert '<script type="module" src="./app.js"></script>' in html


def test_semantic_structure_has_one_h1_four_views_and_disclosure():
    tags = _parse()
    assert sum(tag == "h1" for tag, _ in tags) == 1
    ids = {attrs.get("id") for _, attrs in tags if attrs.get("id")}
    assert {"inbound-view", "task-view", "exception-view", "inventory-view"} <= ids
    html = HTML.read_text(encoding="utf-8")
    assert "Personal WMS/WCS portfolio case study using synthetic data." in html
    assert "WCS behavior and device events are simulated." in html
    assert '<main id="main-content">' in html
    assert '<nav aria-label="Demo views">' in html


def test_form_controls_are_labelled_and_actions_use_native_buttons():
    tags = _parse()
    labels = {attrs.get("for") for tag, attrs in tags if tag == "label" and attrs.get("for")}
    controls = {
        attrs.get("id")
        for tag, attrs in tags
        if tag in {"input", "select", "textarea"} and attrs.get("id")
    }
    assert controls
    assert controls <= labels
    assert sum(tag == "button" for tag, _ in tags) >= 8
    assert all(tag not in {"div", "span", "a"} or "onclick" not in attrs for tag, attrs in tags)


def test_live_status_navigation_and_metric_definitions_are_explicit():
    tags = _parse()
    assert any(
        attrs.get("id") == "live-status"
        and attrs.get("role") == "status"
        and attrs.get("aria-live") == "polite"
        for _, attrs in tags
    )
    nav_buttons = [
        attrs for tag, attrs in tags
        if tag == "button" and attrs.get("data-view")
    ]
    assert {attrs["data-view"] for attrs in nav_buttons} == {
        "inbound-view", "task-view", "exception-view", "inventory-view"
    }
    html = HTML.read_text(encoding="utf-8")
    for text in (
        "Completion Rate = completed / dispatched",
        "Exception Rate = ever failed or timed out / dispatched",
        "First Pass Success = completed with zero retries / dispatched",
        "Average Simulated Cycle Time = completed time minus first dispatch time",
    ):
        assert text in html


def test_accessibility_and_responsive_css_controls_are_present():
    css = CSS.read_text(encoding="utf-8")
    assert ":focus-visible" in css
    assert "font-size: 16px" in css
    assert "@media" in css
    assert "prefers-reduced-motion" in css
    assert "linear-gradient" not in css


def test_app_wires_the_public_domain_interface_and_demo_scenarios():
    app = APP.read_text(encoding="utf-8")
    for call in (
        "createWarehouse",
        "receivePallet",
        "assignLocation",
        "dispatchTask",
        "applyWcsEvent",
        "retryTask",
        "cancelTask",
        "getMetrics",
        "getAuditTrail",
    ):
        assert call in app
    for scenario in ("happy", "offline", "duplicate"):
        assert f'data-scenario="{scenario}"' in HTML.read_text(encoding="utf-8")


def test_header_credits_the_author_and_links_to_the_ba_documents():
    html = HTML.read_text(encoding="utf-8")
    assert "By Ha Quang Huy" in html
    links = [attrs for tag, attrs in _parse() if tag == "a" and attrs.get("href") == REPO_URL]
    assert len(links) == 1
    assert links[0].get("target") == "_blank"
    assert links[0].get("rel") == "noopener noreferrer"
    assert "View BA documents on GitHub" in html


def test_social_preview_and_favicon_use_files_shipped_with_the_demo():
    meta = {
        attrs.get("property") or attrs.get("name"): attrs.get("content")
        for tag, attrs in _parse()
        if tag == "meta"
    }
    assert meta["og:type"] == "website"
    assert meta["og:url"] == DEMO_URL
    assert meta["og:title"] and meta["og:description"]
    assert meta["og:image"] == DEMO_URL + "og-image.png"
    assert meta["twitter:card"] == "summary_large_image"
    html = HTML.read_text(encoding="utf-8")
    assert '<link rel="icon" href="./favicon.svg" type="image/svg+xml">' in html
    assert (PROTOTYPE / "og-image.png").stat().st_size > 10_000
    assert (PROTOTYPE / "favicon.svg").is_file()


def test_prototype_contains_no_private_or_local_material():
    combined = APPROVED_URL.sub("", "\n".join(path.read_text(encoding="utf-8") for path in (HTML, CSS, APP)))
    for pattern in (
        r"(?i)kakadata",
        r"(?i)kakaonline",
        r"(?i)minh\s*tu[aấ]n",
        r"(?i)acerpure",
        r"(?i)github\.com",
        r"(?i)[A-Z]:\\Users\\",
        r"(?i)(api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]",
    ):
        assert re.search(pattern, combined) is None, pattern
