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
not always agree.

**The register of the person's own language area comes first**: GND for the
German language area, BnF for the French, BN for the Polish, LCNAF for the
English. Where that register has no record for the person, take the first of
these that does:

1. **LCNAF** — `id.loc.gov/authorities/names/`
2. **GND** — `d-nb.info/gnd/` (read the `preferredName` from `lobid.org/gnd/`)
3. **BnF** — `catalogue.bnf.fr` or `data.bnf.fr` (UNIMARC field 200, `$a` and
   `$b`; the date qualifier sits in `$f` and is dropped)
4. **BN** — `dbn.bn.org.pl`
5. **Any other register the VIAF cluster gathers**, when none of the four holds
   the person. Ferry van Delden is known only to the Dutch national thesaurus,
   whose heading `Delden, Ferry van` the cluster carries as its main one. Name
   the register in `authorityUrl` so that the heading's origin stays visible.

The library that catalogues a person in their own language is the better
authority for the form of their name. The general order would have given Róża
Etkin the Germanised `Etkin, Rosa`; it equally gives `Guenther, Felix` for Felix
Günther, `Nazelles, R.` where BnF spells out René, and — for Zygmunt Wiehler —
`Wiehlera, Zygmunta`, a Polish genitive that the Library of Congress read off a
title page, where GND and BN both give `Wiehler, Zygmunt`.

The rule is about the form of a name, not about who is the better cataloguer.
Where the language-area register holds no record, the order above applies from
the top, and a heading taken from it is transcribed as it stands.

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
