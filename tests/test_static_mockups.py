"""Static terminal HTML must remain a branded mockup, not an execution simulator."""
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEGACY = ROOT / "frontend" / "legacy"


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.images = []
        self.stylesheets = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append(tag)
        if tag == "img":
            self.images.append(attrs.get("src", ""))
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.stylesheets.append(attrs.get("href", ""))


class StaticMockupTests(unittest.TestCase):
    def test_both_mockups_have_watermark_and_no_script(self):
        for filename in ("21-haiku-desk.html", "22-haiku-core.html"):
            with self.subTest(filename=filename):
                content = (LEGACY / filename).read_text(encoding="utf-8")
                parser = Tags()
                parser.feed(content)
                self.assertIn("@alpha404ai", content)
                self.assertIn('class="watermark"', content)
                self.assertNotIn("script", parser.tags)
                self.assertNotIn("button", parser.tags)
                self.assertNotIn("input", parser.tags)
                self.assertNotIn("select", parser.tags)
                self.assertNotIn("form", parser.tags)
                self.assertNotIn("canvas", parser.tags)
                self.assertNotRegex(content, r"\b(?:Math\.random|requestAnimationFrame|setInterval|setTimeout|K\.boot|Sim\()\b")
                self.assertIn("STATIC", content)
                self.assertIn("NO", content)
                for image in parser.images:
                    self.assertTrue((LEGACY / image).resolve().is_file(), image)
                for css in parser.stylesheets:
                    self.assertTrue((LEGACY / css).resolve().is_file(), css)

    def test_legacy_styles_are_static(self):
        css = (LEGACY / "mockup.css").read_text()
        self.assertNotIn("@keyframes", css)
        self.assertNotIn("animation:", css)
        self.assertIn(".watermark", css)


if __name__ == "__main__":
    unittest.main()
