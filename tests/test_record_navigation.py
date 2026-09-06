from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def node_binary() -> str | None:
    node = shutil.which("node")
    if node:
        return node
    bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
    return str(bundled) if bundled.is_file() else None


class RecordNavigationMarkupTests(unittest.TestCase):
    INDEXES = {
        "work": ("works.html", "Works"),
        "person": ("people.html", "People"),
        "media": ("media.html", "Media"),
        "source": ("sources.html", "Sources"),
        "event": ("life.html", "Timeline"),
        "place": ("map.html", "Map"),
    }

    def test_every_indexed_record_type_has_a_prerendered_breadcrumb_and_back_link(self) -> None:
        for record_type, (filename, label) in self.INDEXES.items():
            pages = sorted((ROOT / "records" / record_type).glob("*/index.html"))
            self.assertTrue(pages, f"no generated {record_type} records")
            text = pages[0].read_text(encoding="utf-8")
            with self.subTest(record_type=record_type):
                self.assertIn('class="record-breadcrumbs" aria-label="Breadcrumb"', text)
                self.assertIn('<a href="index.html">Home</a>', text)
                self.assertIn(f'<a href="{filename}" data-record-index-link>{label}</a>', text)
                self.assertIn(f'<a class="record-back-link" href="{filename}" data-record-back-link>', text)
                self.assertIn('aria-current="page"', text)

    def test_organization_record_does_not_link_to_a_nonexistent_index(self) -> None:
        pages = sorted((ROOT / "records" / "organization").glob("*/index.html"))
        self.assertTrue(pages, "no generated organization records")
        text = pages[0].read_text(encoding="utf-8")
        self.assertIn('class="record-breadcrumbs" aria-label="Breadcrumb"', text)
        self.assertIn("<li><span>Organization</span></li>", text)
        self.assertNotIn("data-record-index-link", text)
        self.assertNotIn("data-record-back-link", text)

    def test_every_filter_page_registers_the_index_it_can_return_to(self) -> None:
        scripts = {
            "assets/site/works.js": "work",
            "assets/site/people.js": "person",
            "assets/site/gallery.js": "media",
            "assets/site/sources.js": "source",
            "assets/site/timeline-20260714.js": "event",
            "assets/site/map-explorer-20260714.js": "place",
        }
        for path, record_type in scripts.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(path=path):
                self.assertIn(f'indexType: "{record_type}"', text)


class RecordReturnStateTests(unittest.TestCase):
    def test_saved_filters_are_restored_but_an_external_destination_is_rejected(self) -> None:
        node = node_binary()
        if not node:
            self.skipTest("Node.js is required to exercise catalogue navigation state")
        module_url = (ROOT / "assets/site/catalogue-filters.js").as_uri()
        script = f"""
          const values = new Map();
          globalThis.document = {{ baseURI: "https://archive.example/" }};
          globalThis.window = {{
            location: new URL("https://archive.example/works.html?type=song&period=european&sort=title"),
            sessionStorage: {{
              getItem: (key) => values.has(key) ? values.get(key) : null,
              setItem: (key, value) => values.set(key, value),
            }},
          }};
          const {{ rememberIndexLocation, recordIndexReturn }} = await import({json.dumps(module_url)});
          rememberIndexLocation("work");
          const restored = recordIndexReturn("work");
          values.set("kaper:index-return:work", "https://malicious.example/collect");
          const rejected = recordIndexReturn("work");
          process.stdout.write(JSON.stringify({{ restored, rejected }}));
        """
        result = subprocess.run(
            [node, "--input-type=module", "--eval", script],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        output = json.loads(result.stdout)
        self.assertEqual(
            output["restored"]["href"],
            "works.html?type=song&period=european&sort=title",
        )
        self.assertTrue(output["restored"]["isFiltered"])
        self.assertEqual(output["restored"]["resolvedBackLabel"], "Back to filtered Works")
        self.assertEqual(output["rejected"]["href"], "works.html")
        self.assertFalse(output["rejected"]["isFiltered"])


if __name__ == "__main__":
    unittest.main()
