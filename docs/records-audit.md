# Records audit, 6 November 2026

An audit of everything in `data/public/v1` other than the Sources, which
`docs/sources-audit.md` covers: 179 People, 299 Works with their 213 Songs,
56 Films and 30 Other Works, 1,330 credits, 204 work relations, 56 timeline
events, 45 places, 410 Media, 237 Organizations, 71 name variants and 67
title variants. The validators already enforce shape, vocabularies,
symmetric links and slugs, and all pass; this audit looks at what they do
not: whether dates agree with each other and with the Sources, whether
certainty matches the evidence, and whether a record cites the evidence its
own note relies on. Each candidate a script raised was read before it was
kept; the ones that did not survive are listed at the end.

## 1. Six credits cite an upload while their note rests on a catalogue the archive holds

Henry König's label lists on musiktiteldb.de are Sources in their own
right: `SRC0742` for Odeon O-11000–O-11999 and `SRC0741` for Electrola
EG 2000–EG 2990. Six credits name the list in their note but do not cite it,
so the card shows only the upload behind them.

| Credit | Song | Note names | Cites |
| --- | --- | --- | --- |
| `CON-S071-P-ORG144` | *Du liebst mich nicht mehr*, Dajos Béla orchestra | König's Odeon list | `SRC0790` (upload, `low`) |
| `CON-S071-LAB-ORG128` | the same, Odeon label | König's Odeon list | `SRC0790` |
| `CON-S080-P-P153` | *Mein Gorilla hat ’ne Villa im Zoo*, Hans Albers | König's Odeon list | `SRC0697`, `SRC0373` |
| `CON-S080-LAB-ORG128` | the same, Odeon label | König's Odeon list | `SRC0697` |
| `CON-S082-P-ORG120` | *In 24 Stunden*, Odeon-Künstler-Orchester | session details from the list | `SRC0698`, `SRC0700` |
| `CON-S038-P-ORG119` | Marek Weber orchestra on Electrola E.G. 2271 | the Electrola list | `SRC0708` |

`SRC0742` itself is linked to no credit at all. The fix is to add the list
to each credit. The two *Du liebst mich nicht mehr* credits, and the
conductor credit beside them (`CON-S071-CON-P205`, whose note says only that
the recording is “catalogued” under Dajos Béla), are three of the four
credits marked `confirmed` on a `low` Source alone; with the list cited, they
rest on a register rather than on the upload.

## 2. Three register entries are rated lower than every other

All but one of the 101 copyright-catalogue Sources and all but two of the
65 Hofmeister entries are rated `high`. The exceptions carry no note saying
why:

- `SRC0212`, *Stay ’way from my arms*, Catalog of Copyright Entries 1932 —
  the entry read on its page during the sources audit.
- `SRC0217`, *Immer, wenn ich glücklich bin*, Hofmeister 1932.
- `SRC0218`, *In 24 Stunden kann soviel geschehn*, Hofmeister 1932.

Unless a reason turns up, they should be `high` like the rest. `SRC0217` is
the only Source of a `confirmed` song-to-film relation (`REL0046`), which
is how it surfaced.

## 3. Nine relations are `confirmed` on Sources rated `medium`

| Relation | Song or film | Linked to | Rests on |
| --- | --- | --- | --- |
| `REL0046`, `REL0047` | *Immer, wenn ich glücklich bin*; *In 24 Stunden* | film *Heut’ kommt’s drauf an* | Hofmeister (finding 2) |
| `REL0077` | *Pourvu qu’on ait vingt ans* | film *Une femme au volant* | Salabert 3384 sheet music |
| `REL0087`, `REL0088` | *Hi-do-ho*; *Love Needs No Inspiration* | short *Two Hearts in Wax Time* | Jurmann catalogue, IMDb |
| `REL0119`–`REL0121` | *Magic*, *Rhumba*, *Tahiti* | *Man of the People* | Jurmann catalogue |
| `REL0214` | film *My Song for You* | as the English version of *Ein Lied für Dich* | Jurmann catalogue, Wikipedia |

The first three are settled by finding 2 and by the printed sheet music,
which names the film on its own cover. The six that rest on the Walter
Jurmann catalogue were searched for during the sources audit and nothing
better was found; they could be held as `probable`, as the credits on the
same evidence elsewhere are. `REL0214` could cite the *Kinematograph Year
Book 1935* (`SRC0962`) only for the film itself, not for the version
relation, so it stays as it is unless a contemporary source says so.

## 4. Dates that disagree

- **`W-S024` *Was macht jede Nacht so ein kleines Baby in der Bar?*** is
  dated 1930, the year of its Hofmeister entry, copyright registration and
  Parlophon recording. Its manuscript in the Kaper Papers (`SRC0888`) is
  signed and dated Berlin 1927. This is the question decided for `O030`,
  where the work's year was kept and the disagreement left visible in the
  Source; the same rule would keep 1930 here.
- **Seven songs are dated 1937 but were registered in 1936.** *Blue Venetian
  Waters*, *A Message from the Man in the Moon*, *Beyond My Fondest Dreams*,
  *Tomorrow Is Another Day*, *The One I Love*, *Keep the Magic of Springtime*
  and *At the Spats and Tennis Club* each have a 1936 entry in the Catalog
  of Copyright Entries, most of them unpublished registrations for films
  released in 1937. A Work's year evidently follows the film or the
  publication, not the first registration, but the rule is written down
  nowhere, and *The One I Love* was registered in February 1936, two years
  before *Everybody Sing*, the film it is credited to. The convention should
  be stated, and that song looked at again.
- **`REL0201`** links *All God’s Chillun Got Rhythm* (1937) to *Birthright*
  (1939), a later film that used it. The relation is right; only the type,
  `associated_with_film`, reads as if the song were written for it.

## 5. People

- **Georges Rey (`P155`) has no credit.** The BnF record of Pathé PA 1234
  (`SRC0625`) credits *O chant d’amour de Tahiti !* to “B. Kaper, W. Jurmann
  and G. Rey, composers”, and his name variant shows he also sang on the
  disc as Tihoti. He is in the dataset for that disc alone, and the disc is
  linked only to *Love Song of Tahiti*, not to the French version *Chanson
  d’amour de Tahiti* (`W-S196`) or to a record of the Tahitian one. Which
  Work the disc carries, and what his part was — adapter, arranger, singer —
  needs deciding before a credit is added.
- **Kaper's roles omit pianist.** Two credits have him as a performer at the
  piano — the Polydor duet with Hermann Bick and the Hamborn piano-quartet
  concert — but his roles are composer, lyricist, arranger and conductor.
- **Three people have one life year.** Gaston Groener (death 1962), Hermann
  Scheibenhofer (birth 1872) and Didier Mauprey (death 1944). The BnF gives
  Mauprey as *18..?–1944* and the GND gives Scheibenhofer's birth alone, so
  two of the gaps are the registers' own; Groener's BnF record could not be
  read from here.
- **Nine people have no authority record**: Oliver Perry, André Roubier,
  Giuliano Pomeranz, H. Hailey-Simpson, A. Oliver, Eleonora Kaper, Eliza
  Rozenblum, Ralph Stanley and Ralph Jack. Several are printed names known
  from one sheet or label, for whom no register may exist; the others are
  worth one search each.

## 6. Smaller items

- **Two places for one building.** `PL010`, the Chopin School of Music in
  the Philharmonic building at Jasna 5, and `PL017`, the Warsaw Philharmonic
  at Jasna 5, share a map point, and `TE0013` links both. They name two
  institutions, which may be intended; if not, `PL017` could fold into
  `PL010`.
- **`TE0043`**, Kaper's solo career at MGM from 1939, rests on one Source,
  the 1975 interview, rated `medium`. Every other event has a `high` Source.
- **`M380`**, *Ach, Otto, Otto...!* sung by Sig Arno, is the one Media whose
  credit line still says the performer is as identified by the uploader.

## Checked and found sound

- **Identity.** No two People share a name; every slug is unique in its
  table.
- **Life and credits.** No credit falls before a person's twelfth year or
  after their death, except Strauss and Tchaikovsky as composers of the
  melodies Kaper set in the *Austrian* and *Russian Cocktails*, which is
  what those credits mean. No timeline event falls outside the life of a
  person it names.
- **Events.** No event ends before it starts or lies after 1939, and every
  Work an event names falls within its span. The thematic events whose Works
  look two years late — the Warsaw songs of 1925–1927, the multilingual films
  of 1931–1933 — run over those years.
- **Works and their records.** Every Work has exactly one Song, Film or
  Other Work record with the same title, year and certainty, and every Work
  has a Source, directly or through a credit. The three Works without a
  Kaper credit are films — *Balalaika*, *Coup de feu à l’aube*, *My Song for
  You* — where his part is a song, carried by the song's own record.
- **Media.** Every local asset file exists, every alt text says something,
  and no Media whose rights are restricted or undetermined is in a gallery.
- **Places.** Every coordinate is valid, every place is used by an event or
  a Media and has a Source.
- **Public text.** No straight quotes, stray whitespace, working notes or
  URLs in the text a page prints; the only hyphenated year ranges are
  authority headings quoted as printed, *Kaper, Bronislaw, 1902-1983*.
- **False leads.** Twenty-two Works whose earliest Source looks older than
  their year are covered by Sources that span several years — the Sirius
  folders of 1927–1933, the *Cocktails* of 1929–1932 — or are films whose
  production was reported before release. *Sonny Boy* (1929) cites the 1928
  score of the song Kaper transcribed, and *Quand une femm’ vous plaque*
  (1931) the 1930 registration of its German original. The fourth credit
  `confirmed` on a `low` Source, Judy Garland in *Everybody Sing*, rests on
  film footage of her singing the number, which the rating of an upload does
  not undo. “XXX” in the rights note of `M444`
  is a volume number. The 85 credits whose role is not among the person's
  roles differ in wording only — *performer* for a singer, *music director*
  for a composer.

## Suggested order of work

1. Cite König's lists on the six credits (finding 1).
2. Raise the three register entries to `high`, unless a reason is found
   (finding 2).
3. Hold the six song-to-film relations that rest on the Jurmann catalogue
   alone as `probable` (finding 3).
4. Add *pianist* to Kaper's roles (finding 5).
5. Decide the year convention and look again at *The One I Love* (finding 4).
6. Decide Georges Rey's credit and which Work Pathé PA 1234 carries
   (finding 5).
7. Search registers for the nine people without one (finding 5).
