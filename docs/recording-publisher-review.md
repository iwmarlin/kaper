# Recording-source publisher review — 26 October 2026

Scope: all eleven `recording_discographic_source` records that still supported
organization-linked `publisher` Contributions after the preceding review.
A recording label may document a music publisher, but its record imprint alone
does not do so. The decision is individual, not a source-type prohibition.

| Source | Examined evidence | Decision |
| --- | --- | --- |
| SRC0008 | Internet Archive photograph of Master MA 137 | No Robbins credit on the label; remove this source from the publisher credit, retain the independent printed evidence. |
| SRC0115 | Salabert 3384 label in the linked transfer | Label separately reads Éditions Echo. Remove the unsupported Salabert publisher Contribution; retain Salabert as record label. Preserve Echo literally on Song, Work, Source and Media without inferring a corporate identity or adding an organization. |
| SRC0695 | Grammophon B 50959 / 22222 label | Retain Roehr: explicit “Verlag: Roehr A.-G., Berlin”. Add recording-label evidence context. |
| SRC0705 | Phonobase record 15273 | Retain Coda: explicit “Éditeur : Coda, Heugel, Paris (1934)”. Add online-catalogue evidence context and reciprocal Coda–Source links. |
| SRC0710 | Electrola E.G. 2400 label | No Edition Karl Brüll publisher credit; retain the independent printed source. |
| SRC0712 | Novaphon B 4051 label | No Wiener Boheme-Verlag publisher credit; retain the independent printed source. |
| SRC0716 | Parlophone 80.235 label | No Wiener Boheme-Verlag publisher credit; retain the independent sources. |
| SRC0717 | Electrola E.G. 2406 label | No Edition Karl Brüll publisher credit; retain the independent printed source. |
| SRC0718 | Electrola E.G. 2259 label | No Alrobi publisher credit; retain the independent printed source. |
| SRC0753 | Kristall 3229 label | No Edition Karl Brüll publisher credit; retain the independent printed source. |
| SRC0754 | Odeon O-11768 b, Be 10147 label | No Monopol-Liederverlag publisher credit; retain the independent printed source. |

The Radiomuseum labels whose video thumbnails show unrelated photographs were examined in
the actual video, not inferred from those thumbnails. The source URLs remain
on the individual records. The high-resolution Salabert and Master label
reproductions were also examined directly. Phonobase explicitly supplies its
publishing statement in catalogue metadata; it is not presented as a direct
reading of the Pathé label.

## Number functions

Electrola labels visibly print 60-1740 (SRC0717) and 60-1496 (SRC0718).
These are retained as label numbers, without an independently established
matrix or take identification. SRC0731's description simply lists 60-1853;
it does not call it a matrix, and the video supplies no disc-label image.
The source and listening-reference descriptions now preserve that limitation.
No session or issue dates were changed in this review.

## Safeguards

`reviewed_publisher_evidence_errors` checks the eleven reviewed publisher scopes
in both graph directions. `reviewed_printed_number_errors` prevents these three
numbers from returning as unqualified matrix statements in Source citations
and Media descriptions/captions. Both run in the public-data validator, with
regression tests including deliberately reintroduced bad links and wording.
