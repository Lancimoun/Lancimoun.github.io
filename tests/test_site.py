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

    def test_reduced_motion_paints_one_frame_instead_of_looping(self) -> None:
        """Under prefers-reduced-motion the hero must settle, not spin in place.

        STRUCTURAL GUARD ONLY -- read what this does and does not prove.

        It proves the *source* keeps a stop path: the reschedule sits behind the
        `running` flag, a cancel exists, and the reduced-motion branch calls
        `frame(...)` directly rather than starting the loop. It does NOT prove
        runtime behaviour; that needs a browser executing rAF against a fronted
        tab, which was not available where this was written, so no runtime claim
        is made here.

        What it is actually protecting, stated precisely because the first
        version of this test protected the wrong thing: under reduced motion the
        rotation and pulses are already frozen, so the loop redrew a
        pixel-identical frame at 60fps forever, for a visitor who had explicitly
        asked their operating system for less motion. That is the real defect.

        It deliberately does NOT assert an IntersectionObserver on the canvas.
        `#net` is `position:fixed; inset:0` and is pinned to the viewport, so it
        never scrolls out of view -- an observer on it always reports intersecting
        and can stop nothing. An earlier pass added one and this test asserted it,
        which meant the suite was enforcing the presence of inert code shaped
        like a guard.
        """
        script = self.html[self.html.find("<script"):]
        self.assertIn("cancelAnimationFrame", script)
        self.assertRegex(
            script, r"if\s*\(\s*running\s*\)\s*rafId\s*=\s*requestAnimationFrame",
            "the frame loop must reschedule only while running",
        )
        self.assertRegex(
            script, r"if\(reduce\)\{[^}]*frame\(performance\.now\(\)\)",
            "reduced motion must paint a single frame rather than start the loop",
        )
        self.assertNotRegex(
            script, r"ctx\.globalAlpha=1;\s*requestAnimationFrame\(frame\);",
            "the old unconditional reschedule is back",
        )

    def test_public_project_links_use_https(self) -> None:
        hrefs = re.findall(r'href="([^"]+)"', self.html)
        external = [href for href in hrefs if not href.startswith(("#", "mailto:", "data:"))]
        self.assertTrue(external)
        self.assertTrue(all(href.startswith("https://") for href in external))


if __name__ == "__main__":
    unittest.main()
