# Authority identifiers and contextual references

An authority identifier says which register holds a record for a person or an
organization. A contextual reference is a page that tells a reader something
about them. The two are kept in separate fields, because only the first is a
claim about identity, and both are structured lists rather than text.

## The two fields

```json
"authorities": [
  { "scheme": "lcnaf", "url": "https://id.loc.gov/authorities/names/n50049756" },
  { "scheme": "gnd",   "url": "https://d-nb.info/gnd/11880300X" }
],
"references": [
  { "label": "Official website", "url": "https://www.slub-dresden.de/" }
]
```

Both are omitted rather than left empty. `authorities` is ordered by the
register precedence below; `references` is ordered by label. No URL repeats
within a field.

This replaces `authorityUrl` and `referenceUrl`, which held the same
information as newline-delimited `Label: URL` text — up to seven identifiers in
one string. Nothing could be read out of that without a regular expression,
and three of them were in the code that rendered it. The field names were
singular for values that were almost always plural.

## The register vocabulary

`scheme` is one of these keys and nothing else. The label in the second column
is what a reader sees; it is held once, in `scripts/authority_identifiers.py`
and in `AUTHORITY_SCHEME_LABELS` in `assets/site/core.js`, and never written
into the data.

| `scheme` | Label | Register |
| --- | --- | --- |
| `lcnaf` | LCNAF | `id.loc.gov/authorities/names/` |
| `gnd` | GND | `d-nb.info/gnd/` |
| `bnf` | BnF | `catalogue.bnf.fr`, `data.bnf.fr` |
| `bn` | BN | `dbn.bn.org.pl`, `data.bn.org.pl` |
| `nukat` | NUKAT | `nukat.edu.pl` |
| `lc_providers` | LC Providers | `id.loc.gov/entities/providers/` |
| `viaf` | VIAF | `viaf.org` |
| `isni` | ISNI | `isni.org/isni/` |
| `wikidata` | Wikidata | `wikidata.org` |
| `musicbrainz` | MusicBrainz | `musicbrainz.org/artist/` |

The first four are the precedence order `docs/authority-headings.md` sets for
transcribing a heading, and `authorities` is sorted in that order so the
registers that may supply a heading come first. LC Providers names corporate
providers rather than people, so it sits outside that head. VIAF and Wikidata
come last because they are hubs: they are used to find which register holds a
record, and neither is ever the source of a heading.

## The scheme is derived, not transcribed

`authority_scheme_for_url` reads the scheme from the URL's host and path. The
label a record arrived with is only used to decide what it was trying to say,
never to decide what the identifier is. A mislabelled identifier therefore
cannot enter the field, and a register cannot acquire a second spelling by
being typed again — which is what had happened: the same Library of Congress
provider register sat in the data as both `LC Providers` and `Library of
Congress Providers`, and the Polish national library as both `BN` and
`Biblioteka Narodowa`.

`authorizedNameSource` stays free text, because it describes where a name was
transcribed from and that is not always a register. Where it does name one, it
uses that register's single label.

## What belongs in `references`

A biographical, archival, filmographic or institutional page: an official
website, a finding aid, a Wikipedia article, a digital-library platform. These
carry their own `label`, because what the page is does not follow from its
host the way `Wikipedia` or `Filmportal` does.

A reference is not an identity claim, so it is never published as schema.org
`sameAs`. The validator rejects a formal authority URL stored as a reference,
and a reference that merely repeats a Source the record already cites.

## Organizations

People were given this separation when the person card was written.
Organizations were not, and until this change twenty-six institutional
homepages, a cooperation agreement, a digital-library platform and a finding
aid sat in the authority field beside LCNAF and GND identifiers. Twenty
organizations appeared to carry authority control while holding no register
record at all.

The field now holds registers for 86 of 159 organizations, and 21 carry
contextual references. People hold registers on 169 of 178 records, between one
and seven each, and 9 carry references.

## An identifier is not a citation

`authorities` links the register record; it does not cite it. Citing it means a
Source of `sourceType: authority_record`, which carries the register's own
dates and can be named on the record it documents — the identifier says where
to look, the Source says the register was consulted and when.

`authoritySubject` says what such a Source documents, and holds `person`,
`work` or `organization`:

| Subject | Needs | `identityRelation` |
| --- | --- | --- |
| `person` | `personIds` | required — a register record either is the same person or is not |
| `work` | `workIds` | must be absent |
| `organization` | `organizationIds` | must be absent |

The third was added when `ORG127` and `ORG141` turned out to be the only two
Organizations citing no source at all while both carried a register
identifier: the document that would have settled them could not be filed.
`SRC0931` cites the GND record for Deutsche Grammophon-AG and `SRC0932` the
LCNAF record for RCA Manufacturing, and every Organization now carries a
source. The other 84 Organizations with register identifiers cite other
documents and were never unsourced, so the same Source is available to them
but not owed.

`identityRelation` is a judgement about whether two descriptions are one
person, which a corporate body does not need and `person_authorities.py` reads
only for people. The validator rejects it on a non-person subject rather than
leaving it to be ignored.

## Where this is enforced

`scripts/authority_identifiers.py` holds the vocabulary, the URL-to-scheme
derivation and the shared shape check. `person_authorities.py` and
`organization_authorities.py` normalize one record each and report the errors
for it; both the exporter and `validate_public_export.py` run those checks, so
a packed string, an unknown scheme, a scheme that disagrees with its URL, a
repeated URL, a list out of precedence order and an authority URL filed as a
reference are all rejected. `normalize_person_authorities.py` and
`normalize_organization_authorities.py` report drift in the canonical files,
and `rebuild_site.py` runs both.
