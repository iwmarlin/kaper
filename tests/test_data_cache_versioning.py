from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicDataCacheVersioningTests(unittest.TestCase):
    def test_tables_use_their_manifest_hash_as_a_cache_key(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is required to exercise the public data loader")

        core = (ROOT / "assets/site/core.js").as_uri()
        script = f"""
          globalThis.document = {{ baseURI: "https://archive.example/sources.html" }};
          const calls = [];
          globalThis.fetch = async (input, options = {{}}) => {{
            const url = String(input);
            calls.push({{ url, options }});
            if (url.endsWith("/manifest.json")) {{
              return {{
                ok: true,
                json: async () => ({{
                  files: [{{
                    file: "sources.json",
                    sha256: "1234567890abcdef1234567890abcdef",
                  }}],
                }}),
              }};
            }}
            return {{ ok: true, json: async () => ({{ records: [{{ id: "SRC0001" }}] }}) }};
          }};

          const {{ loadTable }} = await import({json.dumps(core)});
          const records = await loadTable("sources");
          process.stdout.write(JSON.stringify({{ calls, records }}));
        """
        result = subprocess.run(
            [node, "--input-type=module", "--eval", script],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)

        self.assertEqual(payload["records"], [{"id": "SRC0001"}])
        self.assertEqual(payload["calls"][0]["options"], {"cache": "no-cache"})
        self.assertEqual(
            payload["calls"][1]["url"],
            "https://archive.example/data/public/v1/sources.json?v=1234567890ab",
        )


if __name__ == "__main__":
    unittest.main()
