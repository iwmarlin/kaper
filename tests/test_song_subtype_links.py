"""A source that links a song's work links the song."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORK_OF_SONG = re.compile(r"W-(S\d+)$")


def records(name: str) -> list[dict]:
    path = ROOT / "data/public/v1" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))["records"]


class SongSubtypeLinkTests(unittest.TestCase):
    """Songs are a subtype of Works and have no page of their own, so the pair
    of links is read by the structured export rather than by a reader: a source
    carried W-S152 in workIds and S152 nowhere. Three hundred and fifty-three
    sources mirrored the pair and twenty-three did not, which is drift and not
    a distinction — SRC0070 and SRC0630 each link two songs' works and listed
    only one of the two songs, which no narrower meaning of songIds would
    produce. Mirroring the rest changed no rendered page.
    """

    #: SRC0306 is the catalogue-level Jurmann source, whose links are curated by
    #: hand: the intake file removes nine songs from it because the entry-group
    #: citation SRC0307 is the finer evidence. Its remaining nine unmirrored
    #: songs are left for that editorial judgement rather than filled in here.
    CURATED = {"SRC0306"}

    def test_a_source_linking_a_song_work_links_the_song(self) -> None:
        songs = {record["id"] for record in records("songs")}
        offenders = []
        checked = 0
        for source in records("sources"):
            wanted = {m.group(1) for w in (source.get("workIds") or [])
                      if (m := WORK_OF_SONG.match(w))} & songs
            if not wanted:
                continue
            checked += 1
            if source["id"] in self.CURATED:
                continue
            missing = sorted(wanted - set(source.get("songIds") or []))
            if missing:
                offenders.append(f"{source['id']}: links W-{missing} without {missing}")
        self.assertGreater(checked, 300, "no song-work sources were checked")
        self.assertEqual(offenders, [], "a source links a song's work but not the song")

    def test_the_pair_is_symmetric(self) -> None:
        by_song = {record["id"]: record for record in records("songs")}
        offenders = []
        for source in records("sources"):
            for song_id in (source.get("songIds") or []):
                song = by_song.get(song_id)
                if song is None:
                    offenders.append(f"{source['id']}: songId {song_id} does not exist")
                elif source["id"] not in (song.get("sourceIds") or []):
                    offenders.append(f"{song_id} does not link back to {source['id']}")
        self.assertEqual(offenders, [], "a song link is one-way")


if __name__ == "__main__":
    unittest.main()
