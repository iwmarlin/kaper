# Nine recording catalogues — review of 26 October 2026

Scope: SRC0300, SRC0583, SRC0625, SRC0741, SRC0742, SRC0801, SRC0802,
SRC0805 and SRC0829. All use the existing `sound_recording_catalogue` type;
no new category, person, work, organization, source or listening medium is
created. Bibliographic item records and compiled label lists remain distinct
in their descriptions and date roles.

## Primary material read

The five BnF public records were reread. Full UNIMARC displays were additionally
examined for Salabert 3382, Pathé PA 1234 and Columbia DF 1610. The two
musiktiteldb label lists were read directly. DNB's web interface returned HTTP
429, but a public SRU response supplied MARC records 380669358 and 381098265.
The library's own field 777 in the former points to Ninon as record 380669366.
Subsequent direct requests for that linked record were rate-limited.

The GHT PDF was not freshly downloaded: HTTP returned 423 and HTTPS failed
certificate-name validation; verification was not disabled. Search-indexed
text of the existing GHT matrix reference corroborates the Ninon entry, but
this is not represented as a fresh full-PDF inspection. SRC0583 explicitly
records that limitation and remains qualified.

## Decisions

- **SRC0300:** retain the explicit reconstructed [1934] issue date from BnF
  fields 210 and 306; disclose the conflicting older encoded 1932 in field 100.
  Remove three direct authorship-credit links not supplied by the record.
  Preserve composer/lyricist evidence from the separate sheet-music and label
  sources. The record's controlled Kaper role is orchestra direction.
- **SRC0583:** correct the primary address to the Ninon record 380669366, using
  DNB's explicit coupling link, not an invented identifier. The previous
  address 380669358 describes Oh Madonna, with Be.10220-2 / WBe.10220-2, and is
  retained as a separately labelled related link. Ninon's Be 10221 and session
  date remain attributed to the GHT matrix discography, not to the wrong DNB
  side. Keep the historical PDF as a supplementary reference, not a primary
  access URL masquerading as the catalogue record.
- **SRC0625:** BnF's [DL 1940] is legal deposit, not a verified issue year.
  The explicit recording date is 23 June 1937, which now supplies the structured
  date with role `recording`. Field 101 confirms Tahitian (`tah`). Rey's
  composer role on the Tahiti side is not extended to the original 1935 song,
  and his composer/lyricist role on Ho'i-maï is not merged with it. Add the
  reciprocal Source–Pathé brand link to the existing organization.
- **SRC0741–SRC0742:** remove volatile row totals from citations. Coverage years
  and copyright stamps are not converted into asserted publication dates.
  These are continuously revised secondary label lists, with row-level
  evidence and separately meaningful session/issue fields.
- **SRC0801–SRC0802:** retain the existing unknown/uncertain issue dating and
  separate specialist chronology. Keep the unordered matrix lists unordered.
  Quote BnF's Jurmann-Kaber and surname-only Lelievre without claiming a new
  label reading or resolving the father–son identity. Lelièvre remains probable.
- **SRC0805:** add the catalogue's CL 5023 and CL 5039 without assigning them to
  individual titles by position alone. Remove two Kaper/Jurmann authorship
  links absent from this entry; independent printed evidence remains. The
  second title does not automatically become a new Kaper work.
- **SRC0829:** retain unknown dating. DNB repeats 15875 in field 028; this does
  not establish a second matrix. Its coupling pointer is record 381098273.
  Add reciprocal composer/lyricist evidence actually stated in field 245.

Four associated Rossi listening-copy descriptions now distinguish collection
identifications from the independently catalogued issues; no exact transferred
pressing or take is certified by the existence of a library catalogue entry.

Semantic validation checks the reviewed source types, the Ninon record address,
the legal-deposit/recording distinction, and both directions of the five
unsupported authorship edges. Regression tests also preserve qualified names,
undated live lists, matrix boundaries and the existing external-media rights.
