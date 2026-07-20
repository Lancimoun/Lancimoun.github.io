"""Provider-free contracts for the static portfolio surface."""

from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"


class _SurfaceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.h1_count = 0
        self.images_without_alt: list[dict[str, str | None]] = []
        self.blank_target_links_without_noopener: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "h1":
            self.h1_count += 1
        if tag == "img" and "alt" not in values:
            self.images_without_alt.append(values)
        if tag == "a" and values.get("target") == "_blank":
            rel = set((values.get("rel") or "").split())
            if "noopener" not in rel:
                self.blank_target_links_without_noopener.append(values.get("href") or "")


class PortfolioSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = INDEX.read_text(encoding="utf-8")
        cls.parser = _SurfaceParser()
        cls.parser.feed(cls.html)

    def test_document_shell_and_discovery_metadata(self) -> None:
        self.assertTrue(self.html.lower().startswith("<!doctype html>"))
        self.assertIn('<html lang="en">', self.html)
        self.assertIn('<meta charset="utf-8">', self.html)
        self.assertIn('name="viewport"', self.html)
        self.assertIn('name="description"', self.html)
        self.assertIn('rel="canonical" href="https://lancimoun.github.io/"', self.html)
        self.assertIn('property="og:title"', self.html)
        self.assertIn('name="twitter:card"', self.html)

    def test_semantics_and_link_safety(self) -> None:
        self.assertEqual(self.parser.h1_count, 1)
        self.assertEqual(self.parser.images_without_alt, [])
        self.assertEqual(self.parser.blank_target_links_without_noopener, [])

    def test_no_external_runtime_assets(self) -> None:
        self.assertNotRegex(self.html, r"<script[^>]+src=")
        self.assertNotRegex(self.html, r'<link[^>]+rel="stylesheet"')
        self.assertNotRegex(self.html, r"url\(['\"]?https?://")

    def test_motion_has_accessible_fallback(self) -> None:
        self.assertIn("prefers-reduced-motion", self.html)
        self.assertIn('<canvas id="net" aria-hidden="true"></canvas>', self.html)
        self.assertIn("if(!reduce)ang+=", self.html)
        self.assertIn("if(\"IntersectionObserver\" in window && !reduce)", self.html)

    def test_pinned_public_claims_are_present(self) -> None:
        """Presence only — this does NOT verify the numbers are true.

        These are hardcoded literals because this repo ships alone: it cannot
        reach the other projects to count their tests. That makes this test a
        guard against a claim being *deleted*, not against it going *stale* —
        and the distinction bit us: LEMMA grew 67 -> 72 tests, and this test's
        literal actively kept the page wrong, because correcting the page broke
        the suite. When a number here changes, update it here too.

        Accuracy is verified outside this repo by `LOOP/audit_frontdoor.py`,
        which cross-checks every figure against the measured fleet record.
        """
        for claim in (
            "72 tests",
            "30 tests",
            "35 tests",
            "2,778 nodes",
            "7,295 connections",
            "157 systems",
            "219",
        ):
            with self.subTest(claim=claim):
                self.assertIn(claim, self.html)

    def test_public_project_links_use_https(self) -> None:
        hrefs = re.findall(r'href="([^"]+)"', self.html)
        external = [href for href in hrefs if not href.startswith(("#", "mailto:", "data:"))]
        self.assertTrue(external)
        self.assertTrue(all(href.startswith("https://") for href in external))


if __name__ == "__main__":
    unittest.main()
