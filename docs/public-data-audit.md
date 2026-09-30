# Public data audit — 30 September 2026

An audit of `data/public/v1/` looking for what the repository's own checks do
not cover. No data was changed. Every finding below was verified against the
canonical tables; the closing section lists the leads that were checked and
found to be sound, so they are not re-investigated.

## Starting position

The repository's own checks all pass on this branch: `reconcile_manifest.py`,
`build_site_assets.py`, `build_record_payloads.py`, `build_static_records.py`,
`validate_public_export.py` and `validate_site.py` each report `ok`, and the
test suite passes 347 tests with 4517 subtests. The audit therefore looked past
them, at the shape of the data rather than its validity.

The dataset holds 178 People, 159 Organizations, 838 Sources, 407 Media, 299
Works (56 Films, 213 Songs, 30 Other Works), 204 Work Relations, 56 Timeline
Events, 45 Places, 1327 Contributions, 70 Person Name Variants and 67 Title
Variants.

## Findings

### 1. `authorityUrl` is a packed text field, not a structured one

192 of the 275 People and Organizations that carry `authorityUrl` hold between
two and seven identifiers in a single newline-delimited string, in the form
`LCNAF: https://…\nGND: https://…\nVIAF: https://…`. One record holds seven.
The field name is singular.

The label before each URI is uncontrolled, and it has already drifted. Seventeen
distinct prefixes are in use. Six are the canonical registers (LCNAF 207, VIAF
166, GND 129, ISNI 60, Wikidata 57, BnF 36); the rest are occasional or
one-off, including `Official website` (21), `MusicBrainz`, `NUKAT`, `CRISPA`,
`Finding aid`, `Digital library` and `Cooperation agreement`. Two registers are
spelled two ways: `BN` (6) alongside `Biblioteka Narodowa` (1), and
`LC Providers` (1) alongside `Library of Congress Providers` (1).

This is the one finding that concerns the data model rather than data coverage,
and it sits oddly against the archive's rigour elsewhere: Source dates were
given a controlled, sortable model with `dateRole` and `dateQualifier` precisely
so that they could be queried and validated, while authority identifiers — the
backbone of the name control this archive rests on — cannot be queried without
a regular expression and are validated per-record only as free text.

Suggested shape: `authorities: [{ "scheme": "VIAF", "uri": "https://…" }]`, a
controlled scheme vocabulary, and a validator that rejects an unknown scheme and
a malformed URI. `Official website` and `Finding aid` are not name authorities
and belong in a separate field.

**Resolved.** `authorities` and `references` are now structured lists with a
closed register vocabulary, and the scheme is derived from the URL rather than
transcribed, so neither drift can recur. The investigation also found that the
uncontrolled labels were not all noise: `id.loc.gov/entities/providers` and the
`data.bn.org.pl` route of the BN register are real registers the vocabulary was
missing, and twenty organizations had appeared to carry authority control while
holding only an institutional homepage. See `docs/authority-identifiers.md`.

### 2. `evidenceContext` is missing along role lines, and no rule states when it applies

`evidenceContext` is filled on 683 of 1327 Contributions (51.5%), but the gap is
not spread evenly — it tracks the role:

| Role | n | missing | % missing |
| --- | --- | --- | --- |
| lyricist | 228 | 208 | 91% |
| film_director | 62 | 58 | 94% |
| composer | 527 | 365 | 69% |
| arranger | 23 | 5 | 22% |
| publisher | 204 | 8 | 4% |
| 12 further roles | 283 | 0 | 0% |

The obvious explanation — that Kaper's own credits need no context in an archive
about Kaper — does not hold. Of the 365 composer credits without context, 160
belong to other composers (Walter Jurmann, Fritz Rotter among them), and
Kaper's own 273 composer credits are themselves split, 68 with context and 205
without. The pattern follows the batch a credit arrived in, not an editorial
rule.

`docs/contribution-certainty.md` sets out what `certainty` means and what it
deliberately does not grade. There is no equivalent statement anywhere in
`docs/` for `evidenceContext`: the string `evidenceContext` does not occur in
the documentation at all. Either it is required and 644 records are behind, or
it is optional and the reason should be written down.

**Neither, as it turns out.** The two alternatives above were the wrong pair.
Of the 683 values, 629 name the kind of document that attested a credit and 45
name what the person contributed — `original_composition`, `film_song`,
`background_music`, `stock_music`, `additional_music` — with 9 compounds
joining two statements with `_and_`. One column answers two questions, so
“required” has no definite meaning until they are separated, and filling 644
records against an uncontrolled 26-value vocabulary would have entrenched the
conflation. Two things were safe to settle now and are done: the dead branch
that would have printed these internal tokens to readers is gone, and the one
value carrying rendering logic is pinned by tests. The rest is an editorial
decision, set out in `docs/contribution-evidence-context.md`.

### 3. Organization authority control lags person authority control

People carry `authorityUrl` on 169 of 178 records (95%). Organizations carry it
on 106 of 159 (67%). The 53 without are not marginal bodies: 23 film studios,
12 record labels and 8 publishers, among them Universal Pictures, Fox Film
Europa, Emelka-Konzern, Cine-Allianz Tonfilm GmbH, Joe May-Film AG and Richard
Oswald-Produktion GmbH.

These are fillable. The Weimar production companies hold GND and filmportal.de
records, and the archive already cites filmportal.de as the primary URL of 34
Sources, so the registers are ones this project already works in.

### 4. 104 Sources name their repository only as free text

834 Sources carry a `repository` string and 731 link an Organization record
through `organizationIds`. The 104 that name a repository without linking one
are not a uniform backlog — two cases are distinct:

Institutions with no Organization record at all. `Universität Hamburg` appears
as a repository string 22 times (the LeXM lexicon, 23 Sources by host) and
`Bundesarchiv, Digitaler Lesesaal` 3 times, and neither has an Organization
record in the dataset. These are repeat-cited institutions that the graph cannot
reach.

Strings that are not institution names. `grammophon-platten.de` stands as the
repository of 5 Sources — a hostname where every Organization record carries an
`authorizedName`. `Filmprogrammhefte-Index (filmprogramm.blogspot.com)` and
`Private collection (commercial listing via eBay)` are the same kind of entry.
Some of these may correctly have no institutional record, in which case the
field is being used for two different things and could say so.

### 5. One address, two Places, two precision categories

`PL010` (Chopin School of Music, Warsaw Philharmonic building, Jasna 5) and
`PL017` (Warsaw Philharmonic, Jasna 5) hold identical coordinates,
52.2359, 21.0107, and different `mapPrecision`: `site_approximate` on PL010 and
`venue_level` on PL017.

Modelling the school and the concert venue as separate records is defensible —
they are different bodies that shared a building. Two different precision
categories for one coordinate pair is not, because `docs/site-architecture.md`
states that precision is an evidential category about how exactly the
coordinates identify a location. The same point cannot be both approximate and
venue-level.

### 6. Two fields carry evidence that the site never shows

Neither of these is read by the renderer, the build, or any validator. Each
appears in `public_export_config.json` and nowhere else in the code:

`contributions.evidenceLocator` (34 records) holds page-level evidence, for
example `Hofmeister 1930, pp. 219 and 226` and `Jazz Drops no. 6, M.V.A. 5824`.
This is the most precise citation data in the archive, and a reader cannot see
it.

`songs.useStatus` (6 records) marks film cues as `unused` — The Hideout, The
Duel, The Next Morning, First Deal, Rhumba, Tahiti. That a cue was composed and
not used is a scholarly statement, and the catalogue does not make it.

This is not the `displayOnSite` case that was removed in c5a1f45. That flag was
dead because it carried no information. These two carry information and are
silently dropped, so the choice is to publish them or to drop them on purpose.

### 6a. The film credit qualification is recorded three times and published none

Found while working finding 2, and the largest reader-facing gap in the
dataset. `films.creditType` says what kind of music credit a film carries —
`composer` (26), `songwriter` (19), `music_direction` (3), `stock_music` (3),
`background_music` (2), `music_score` (1), `uncertain` (1), on 55 of 56 films —
and `films.attributionNote` gives it in prose on 31 of them. Neither is
rendered. Neither is read by any code at all: the strings occur in
`films.json`, they are carried into the record payload the browser downloads,
and no template, renderer or script mentions them.

The consequence is on the page. A reader opening *Mutiny on the Bounty* sees
Kaper under a confirmed `composer` credit, with Year and Period beside it and
nothing else. The archive's own data says `creditType: songwriter` and “Song
‘Love Song of Tahiti’ (m. Kaper & Jurmann, lyric Gus Kahn) — uncredited on
screen”. *A Night at the Opera* holds “score by Herbert Stothart; songs by
Kaper”, which appears in no rendered page; the string exists in exactly two
files, the canonical table and the generated payload. On the 19 songwriter
films and the 3 stock-music ones, a reader cannot tell a song credit from a
score credit.

This is finding 6 again — substance exported and never shown — but at 55 and
31 records rather than 34 and 6, and carrying a scholarly qualification rather
than a locator.

**Resolved.** The card now states the credit where it is not the plain one, in
the “Kaper attribution” row the context-only works already used: Songwriter on
19 films, Music direction and Stock music on 3 each, Background music on 2,
Music score and Unresolved on 1 each. A plain `composer` credit stays silent,
as an authorized name does where it matches the title. All 31 attribution notes
are shown as editorial context beside the description.

### 6b. The export overrides have fallen 262 fields behind the canonical data

Found while working finding 2. `scripts/public_export_overrides.json` holds 780
auditable corrections, each with a written reason, and the manifest records its
checksum and counts as a public input. Compared field by field against
`data/public/v1/`, 1819 of its values match the data, 34 differ only in
typography, and **277 differ substantively**. Fifteen of those 277 are the
`authorityUrl` entries, which now differ by design: the field is the intake
name that the authority normalizer consumes, so the override supplies the
legacy packed form and the output holds `authorities`. That leaves 262
substantive divergences that predate this branch, 202 of them in Sources —
`fullCitation` 87, `date` 41, `url` 38, `researchNote` 8, `title` 8, `creator`
6, `repository` 5. Eleven `removeFields` name a field the record still carries,
and eight overrides name a record that no longer exists at all: REL0170,
W-S204, S204, SRC0192, CON-F032-SM-P009, CON-S190-C-P009, PNV0014, TV0296.

The direction of the drift is consistent: the canonical data has been edited
forward and the override file kept the earlier text. `W-S097.sortTitle` is
`À Paris tiguidiguidi` in the data and `Paris tiguidiguidi` in the override,
from before the filing-title rule; `O012.sourceIds` has gained `SRC0789`;
`F052.attributionNote` is a fuller text in the data than the override carries.

This is not a contradiction of the documented model — `data/public/v1/` is the
source of truth, and `reconcile_manifest.py` exists precisely for the case
where the full export was not re-run. It is a loaded gun rather than a present
error: running `export_public_data.py` against the private source package today
would silently revert 262 curated fields and fail on eight missing records. The
one thing keeping that harmless is that its entrypoint is unused, which
finding 1's investigation had already established.

Either the overrides are reconciled to the data, or the export path is marked
as historical and the file with it. Leaving both in place, with the manifest
presenting the overrides as a live public input, is the state that invites the
accident.

### 7. Two songs titled `Adieu` need an editorial ruling

`W-S091` (1933, four Sources) and `W-S186` (1935, one Source) share the title
exactly, and neither carries `lyricistAsPrinted`, `publisherAsPrinted` or
`genre`. They are either two works or one work catalogued twice from two
different sources. The other repeated titles are sound: `San Francisco`
(`W-F043` film 1936, `W-S130` song 1936, `W-S218` song 1937) and the other
film/song pairs are a film and its title song.

### 8. Smaller items

- 21 Media with `galleryStatus: selected` carry no `description`, all images,
  mostly director and performer portraits (M242 Duke Ellington, M247 W. S. Van
  Dyke, M249 Max Ophüls among them). These are the ones the gallery puts
  forward. `altText`, `publicCaption`, `publicCreditLine` and `rightsNote` are
  complete on all 407 records, so this is the only gap in media metadata.
- 9 Sources still use `http://`: `landesarchiv-berlin.de`, `musiktiteldb.de`
  (6), `kppg.waw.pl`. Not a delivery risk on a static site under the
  `netlify.toml` policy, but out of step with the other 823.
- `ORG127` (Deutsche Grammophon-Aktiengesellschaft) and `ORG141` (RCA
  Manufacturing Company) are the only two Organizations with no `sourceIds`.
  Both exist solely as corporate parents, reached through
  `parentOrganizationIds` from Grammophon, Polydor and Victor. That parent
  relation is a historical claim and it is the one assertion in the dataset
  with no source behind it.
- 3 Sources have neither `primaryUrl` nor `repository`, so a reader cannot
  reach them: `SRC0373` (Buxbaum, Wien 2006), `SRC0490` and `SRC0491`
  (Lindstedt). `SRC0491` is marked forthcoming for 2026 and will need revisiting.
- 3 People have no `authorizedNameSource`: P106 Charlie Davson, P108 Didier
  Mauprey, P155 Georges Rey.
- 23 of 30 Other Works have no `shelfmark`, and 32 of 56 Films no
  `titleVariantIds`.

## Checked and found sound

These were investigated and are not defects. They are recorded so that the same
ground is not covered again.

- **No orphaned records.** An early pass appeared to find 123 unreachable Media
  and 54 unreachable Organizations. That pass was wrong: it omitted
  `sources.json` when collecting inbound references. Sources carry `mediaIds`,
  `organizationIds`, `personIds`, `workIds`, `songIds` and `contributionIds`,
  and once those are counted every record in every table is reachable. ORG062
  alone is cited by 81 Sources.
- **The 39 repeated `primaryUrl` values are correct.** Every group is
  distinguishable by citation, date or title. Seven Sources share one Hofmeister
  catalogue page because that page lists seven separate entries, each recorded
  with its own page number and title. This is the right way to cite a catalogue.
- **`lifeDatesSourceIds` at 8 of 178 records is policy, not a gap.**
  `docs/person-life-dates-review.md` states that the note and its evidence are
  required for `disputed` dates, `scripts/person_life_dates.py` enforces it in
  both the exporter and the validator, and all 7 disputed People carry both.
- **`sources.identityRelation` (23 records) and `media.assetCount` (344) are
  live.** `authority_sources.py` sets and validates `identityRelation` against a
  controlled vocabulary and `person_authorities.py` reads it;
  `export_public_data.py` checks `assetCount` against the length of
  `assetPaths`. Both are rare by design, not abandoned.
- **Link symmetry is intact.** Eleven directed pairs were tested, including
  Works/Contributions, People/Contributions, Places/Timeline Events,
  Works/Sources, Media/Works, Sources/Organizations, Sources/People and
  Sources/Media. No asymmetry in any direction.
- **Scope and life dates hold.** No Work, Film, Song or Other Work falls outside
  1902–1939, every one of the 299 Works carries a year, all 56 Timeline Events
  carry `dateStart` within 1902–1939, and no person has an impossible or
  implausible life span.
- **Media rights metadata is complete.** All 407 records carry
  `publicCreditLine`, `rightsNote`, `altText`, `publicCaption`, `rightsStatus`
  and a reachable asset or `externalUrl`.
- **Source coverage is effectively total.** Twelve of thirteen tables cite a
  source on every record; Organizations is the single exception, at 157 of 159.
- **Place precision is documented.** All 29 approximate or area-level Places
  carry a `publicNote`, as `docs/site-architecture.md` requires.
- **M195 and M294 sharing an `externalUrl` is correct.** They are the full
  reception photograph and a detail of one guest within it.
- **The 10 People with no Contributions are reachable.** All are linked from
  Timeline Events and Sources.

## Suggested order of work

1. ~~Restructure `authorityUrl` into `authorities: [{scheme, uri}]` with a
   controlled vocabulary and a validator (finding 1).~~ Done — it changed the
   schema, so it landed before more identifiers could be added to the packed
   field. Everything below is data entry or an editorial decision.
2. Decide whether `evidenceContext` separates into an evidential field and a
   field for the nature of the contribution (finding 2). The rule for when it
   is required depends on that answer, so it comes first; what the field holds
   today, and the two fixes that did not need the decision, are in
   `docs/contribution-evidence-context.md`.
3. Resolve `PL010`/`PL017` precision, the two `Adieu` works, and the ORG127 and
   ORG141 parent claims (findings 5, 7, 8) — small, each a single editorial
   decision.
4. Decide whether `evidenceLocator` and `useStatus` are published or dropped
   (finding 6).
5. Create Organization records for Universität Hamburg and the Bundesarchiv and
   link the repeat-cited repositories (finding 4).
6. Fill organization authority identifiers, starting with the Weimar studios
   (finding 3).
7. Sweep the smaller items (finding 8).
