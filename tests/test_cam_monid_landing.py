from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
LANDING = ROOT / "docs" / "showpieces" / "cam-codx-monid" / "index.html"
BRIEF = ROOT / "docs" / "CAM_CODEX_MONID_OWNER_BRIEF.md"
REQUIRED_SECTIONS = {
    "capability-flow",
    "catalog",
    "showcases",
    "division-of-labor",
    "proof",
    "explore",
}
SHOWCASE_NAMES = (
    "Capability Spike",
    "Launch Week",
    "Competitive Surface",
    "Product Intelligence",
    "Incident Context",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing public artifact: {path.relative_to(ROOT)}"
    return path.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return " ".join(text.lower().split())


class LandingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title = ""
        self.h1_count = 0
        self.section_ids: set[str] = set()
        self.links: list[str] = []
        self.meta_description = ""
        self.showcase_count = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = dict(attrs)
        if tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "section" and values.get("id"):
            self.section_ids.add(str(values["id"]))
        elif tag == "a" and values.get("href"):
            self.links.append(str(values["href"]))
        elif tag == "meta" and values.get("name") == "description":
            self.meta_description = str(values.get("content", ""))
        if "data-showcase" in values:
            self.showcase_count += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data


def _landing_parser() -> tuple[str, LandingParser]:
    html = _read(LANDING)
    parser = LandingParser()
    parser.feed(html)
    return html, parser


def test_landing_has_semantic_campaign_structure_and_five_showcases() -> None:
    html, parser = _landing_parser()

    assert parser.h1_count == 1
    assert 10 <= len(parser.title.strip()) < 60
    assert 40 <= len(parser.meta_description.strip()) < 160
    assert REQUIRED_SECTIONS <= parser.section_ids
    assert parser.showcase_count == 5
    assert all(name in html for name in SHOWCASE_NAMES)
    assert 'name="viewport"' in html
    assert "prefers-reduced-motion" in html
    assert ":focus-visible" in html


def test_landing_links_to_source_guide_and_dated_receipt() -> None:
    _html, parser = _landing_parser()
    required = {
        "../../CAM_MONID_SHOWCASE_SKILLS.md",
        "../../reports/2026-09-02-monid-showcase-catalog.md",
        "https://github.com/deesatzed/CAM_Codx/tree/feat/monid-showcase-skills",
    }
    assert required <= set(parser.links)

    for href in parser.links:
        parsed = urlparse(href)
        if parsed.scheme or href.startswith(("#", "mailto:")):
            continue
        target = (LANDING.parent / parsed.path).resolve()
        assert target.exists(), f"broken local landing link: {href}"


def test_public_artifacts_state_exact_live_fixture_and_not_claimed_boundaries() -> None:
    html = _normalized(_read(LANDING))
    brief = _normalized(_read(BRIEF))

    for text in (html, brief):
        assert "five authenticated" in text
        assert "monid discover" in text
        assert "fixture-tested" in text
        assert "paid endpoint executed" in text
        assert "none" in text
        assert "live monid inspect" in text
        assert "not" in text
        assert "production application" in text

    assert "exercised live" in html
    assert "not claimed" in html
    assert "six skill packages" in html


def test_public_artifacts_exclude_secrets_private_concepts_and_false_endorsement() -> None:
    combined = _read(LANDING) + "\n" + _read(BRIEF)
    lowered = combined.lower()

    assert "/Volumes/" not in combined
    assert not re.search(r"monid_(?:live|test)_[a-z0-9_-]+", combined, re.IGNORECASE)
    assert not re.search(r"api[_-]?key\s*=", combined, re.IGNORECASE)
    for forbidden in (
        "scotch",
        "maya",
        "testimonial",
        "official monid partner",
        "in partnership with monid",
        "endorsed by monid",
        "we executed a paid endpoint",
        "production-ready monid application",
    ):
        assert forbidden not in lowered


def test_owner_brief_is_sendable_and_answers_real_credential_question() -> None:
    brief = _read(BRIEF)
    normalized = _normalized(brief)
    for heading in (
        "## Ready-to-send email",
        "## Executive summary",
        "## The problem we addressed",
        "## What we built",
        "## How the architecture works",
        "## What used a real Monid credential",
        "## Verification and evidence",
        "## Why this matters to Monid",
        "## Boundaries and next proof",
        "## Links",
    ):
        assert heading in brief
    assert brief.count("### Subject option") == 2
    email = brief.split("## Ready-to-send email", 1)[1].split(
        "## Executive summary", 1
    )[0]
    assert 80 <= len(email.split()) <= 250
    assert "token value" in normalized
    assert "never printed" in normalized
