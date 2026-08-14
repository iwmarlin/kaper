# Authorized headings for people

`authorizedName` holds the heading of a person as an authority file states it,
not a form composed for this archive. `displayName` stays as the archive
presents the person; the two differ on purpose.

## Transcription rule

Transcribe the heading verbatim from the authority record, then strip the date
qualifier. `Kiepura, Jan, 1902-1966` is recorded as `Kiepura, Jan`; life dates
live in `birthYear` and `deathYear`, where they can be queried.

Keep the inverted form, the punctuation and the diacritics of the register.
Particles follow the register: BnF gives `Poligny, Serge de`, and that is what
the field holds.

## Precedence when registers disagree

A VIAF cluster gathers the headings of every contributing library, and they do
not always agree. Take the first register that has a record for the person:

1. **LCNAF** — `id.loc.gov/authorities/names/`
2. **GND** — `d-nb.info/gnd/` (read the `preferredName` from `lobid.org/gnd/`)
3. **BnF** — `catalogue.bnf.fr` or `data.bnf.fr` (UNIMARC field 200, `$a` and
   `$b`; the date qualifier sits in `$f` and is dropped)
4. **BN** — `dbn.bn.org.pl`

VIAF itself is never the source of a heading. It is a hub: use it, or Wikidata,
to find which register records belong to the person, then read the heading from
that register.

## Locally constructed headings

Where no register holds the person, a heading may be constructed in the same
inverted form from the documents this archive already cites. Such a heading
must be marked as local, so that a reader can tell a transcription from an
editorial decision. Do not construct a heading from a name that appears only in
one printed credit; a person documented that thinly may not warrant a person
record at all.

## Provenance

Record which register a heading came from in the person's `authorityUrl`, which
is where the identifier for that register is already kept.
