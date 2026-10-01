import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# A YouTube credit names the performers and the original carrier where they are
# known, then the channel that published the copy. Official reissues on
# auto-generated "Topic" channels name the distributor instead of an uploader.
UPLOAD = re.compile(r"(?:^|[.”] |Still from a )YouTube upload by [^;]+?(?:, \d{1,2} \w+ \d{4})?\.$")
PROVIDED = re.compile(r"; [^;]*℗ [^;]+\. Provided to YouTube by [^()]+ \(channel “[^”]+ - Topic”\)\.$")


class YouTubeCreditLineTests(unittest.TestCase):
    def test_every_youtube_medium_names_its_channel_in_house_style(self) -> None:
        records = json.loads((ROOT / "data/public/v1/media.json").read_text(encoding="utf-8"))["records"]
        youtube = [m for m in records if "youtu" in (m.get("externalUrl") or "")]
        self.assertTrue(youtube)
        for medium in youtube:
            credit = medium.get("publicCreditLine") or ""
            with self.subTest(media_id=medium["id"]):
                self.assertTrue(UPLOAD.search(credit) or PROVIDED.search(credit), credit)
                self.assertNotRegex(credit, r"listening link|access copy|external (?:YouTube )?transfer")


if __name__ == "__main__":
    unittest.main()
