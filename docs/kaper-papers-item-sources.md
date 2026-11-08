# Kaper Papers — one Source per manuscript, 5 November 2026

## Why there were two models

The Bronislaw Kaper Papers (Collection 03193, American Heritage Center,
University of Wyoming) were cited in two ways. `SRC0009`, from the first
export of 14 July, stood for the whole group of early manuscripts: seven Other
Works, the song *Hätt’ ich einen Kammerdiener?*, five audio references, two
timeline events, three name variants and eighteen credits, under one
citation with no date. Every
Kaper Papers Source added since was made per item — *Denkst Du noch an jeden
Tag* (`SRC0709`), *Was macht jede Nacht* (`SRC0888`), *Jazz Drops*
(`SRC0775`) and the *Cocktails* cover (`SRC0789`) — because each was written
when that manuscript was examined. The collective record was never revisited,
so the Sources list showed two songs as manuscripts of their own and the early
works as one entry.

Item level is what the repository asks for. The Archives West guide gives the
preferred citation as *Item Description, Box Number, Folder Number, Collection
Name, Collection Number*, and the Center's accession list of 19 March 1970,
signed by Gene M. Gressley, describes each manuscript separately, with place,
date and number of leaves. Its margin carries handwritten *Box 1* and *Box 2*
braces, and they agree with every box the works already recorded.

## What was done

`SRC0953`–`SRC0959` cite one manuscript each. The title and year follow the
Work; the description quotes the accession list, and where the list names the
piece differently its own wording is given:

| Source | Work | Accession list, 1970 | Box |
| --- | --- | --- | --- |
| SRC0953 | O001 *Rozmowa* | Warsaw, 1923; 3½ leaves | 2 |
| SRC0954 | O002 *Koszutski Girls* | Valse, Warsaw, 1923; 2 leaves | 1 |
| SRC0955 | O003 *Etude for Piano* | Warsaw, 1925; 2½ leaves | 1 |
| SRC0956 | O005 *Sonatina for Piano* | “Sonetine for Piano”, Warsaw, 1927; 14 leaves | 2 |
| SRC0957 | O006 *Piece for 8 Violins and Piano* | “Untitled: Composition for 8 violins and piano, Berlin, 1927”; 20 leaves | 2 |
| SRC0958 | O030 *Piece for Voice and Orchestra* | “Untitled: Piece for voice and orchestra, Berlin, 1926”; 8 leaves | 2 |
| SRC0959 | S004 *Hätt’ ich einen Kammerdiener?* | Lied and fox-trot, Berlin, 1926; 2 leaves | 1 |

Each credit, audio reference, timeline event and name variant moved to the
Source of the manuscript it rests on, and nothing else in those records
changed. `SRC0009` keeps its identifier and becomes the Source for O004
*Piece for Orchestra*, the one manuscript the accession list does not
describe; it still links the Archives West guide. `SRC0888` gains its box, 2,
from the same braces. `tests/test_kaper_papers_item_sources.py` holds the
rule: one Source per manuscript, the box it cites matching the work's.

## Decided, and still open

- **O030 is dated 1928; the accession list says Berlin, 1926.** Decided: the
  work's year stands. Its Source carries 1928 marked uncertain and quotes the
  list, so the disagreement is visible rather than resolved.
- **The *Polka* the list describes** (holograph, signed, 5 leaves, undated)
  is out of scope and gets no record.
- **O005's Other Work record cites `SRC0503`, its Work record does not.**
  Decided: left as it is.
- **Holding credits.** The review first said *Hätt’ ich einen Kammerdiener?*
  lacked a holding statement. It did not: songs have no holding fields, and
  record where a manuscript is through a `holding_institution` credit, which
  S004 has. The gap was the other way round. *Denkst Du noch an jeden Tag* and
  *Was macht jede Nacht*, added later, had no such credit, so their cards did
  not say where the manuscript is. `CON-S012-HI-ORG056` (box 1) and
  `CON-S024-HI-ORG056` (box 2) now do, each resting on its manuscript Source.
- **Settled, 8 November 2026: O004 shares O030's folder.** The list's single
  entry *Piece for voice and orchestra, Berlin, 1926*, 8 leaves, describes one
  folder, scanned by the Center as “Box 2, Untitled Orchestra for Voice”. Its
  first four pages hold the *Piece for Orchestra*, headed “written in Warsaw,
  1926”, a fragment of little more than one page; the other eight hold the
  *Piece for Voice and Orchestra*, headed Warsaw, struck through, Berlin,
  1928, which opens with the same flute figure. The list took the scoring
  from the later piece and the date from the earlier. `SRC0009` now cites the
  folder and the accession list like the other manuscript Sources, and its
  note and `SRC0958`'s say what the folder holds.
