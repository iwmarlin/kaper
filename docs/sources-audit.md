# Sources audit, 5 November 2026

An audit of the 863 Sources in `data/public/v1/sources.json`: what a reader
can reach from each one, what each record rests on, and whether the public
text is clean. Every link was requested, not inferred. Each finding below
survived a check designed to disprove it; the leads that did not are listed
at the end, so they are not chased again.

Scope: all 863 records and all 844 distinct URLs they carry in `primaryUrl`,
`accessUrl` and `additionalLinks`. The validators already enforce record
shape, controlled vocabularies, symmetric links and slugs, and all pass; this
audit looks at what they do not check.

## 1. A catalogue citation often lands on the whole volume

The largest reader-facing gap. A Source can name the exact page or entry and
still link the volume's front door, so the reader has to search a
several-hundred-page scan for it.

| Catalogue | Sources | Locator in the citation | Link goes to the entry |
| --- | --- | --- | --- |
| Hofmeister, *Monatsbericht*, via ANNO | 69 | page, in 68 | 12 (`&seite=`) |
| *Catalog of Copyright Entries*, via the Internet Archive | 89 | entry or registration number, in all 89 | 4 (`/page/`) |
| GEMA repertoire search | 6 | work number, in all 6 | 0 |

So 57 Hofmeister and 85 copyright-catalogue Sources link the issue or
volume when the citation already says where the entry is, and the six GEMA
Sources (`SRC0292`–`0295`, `SRC0885`, `SRC0891`) link an empty search form.

The two catalogues can be fixed. ANNO addresses a scan page with `&seite=`,
which is the scan index rather than the printed page, so each volume needs
its own offset, read once from one known page. The Internet Archive addresses
a scan page with `/page/nNNN`, and each entry can be found through the item's
full-text search. GEMA's portal has no permanent link to a work; the work
number in the citation is already the most a reader can be given, and the
record could say so. *Done:* all six now say so in their verification note.

**Copyright catalogue: all 89 now open on their page.** Each entry was
found through the volume's full-text search and accepted only when two
signals agreed on one scan: its registration number in its own series —
*E for.* is not *E unp.*, and the first draft accepted both and matched
*E for. 5136* to an unrelated *E unp. 5136* — and its title on the same or
the next scan. Single-signal matches were read one by one; one of them,
`SRC0263`, was a different song sharing the phrase *a message from*, and was
rejected. Links use the scan index (`/page/nNNN`), taken per volume from the
item's `scandata.xml`, not the printed page number. The printed labels
Internet Archive derives in `page_numbers.json` are wrong in places — in
volume 25 they run twelve pages off — and the first comparison, which
trusted them, wrongly called the four existing page links misplaced. Read
against the scans, all four are right, and they are unchanged. Five new links
were read against the scan image before the rest were written, and one,
`SRC0212`, lands on page 906, the page its own citation gives.
**The last 22 were placed by entry number.** Each volume numbers its entries
in one run, and the number is printed after each entry, so an entry number
in the citation is a third signal: an entry is accepted on the scan that
carries its number together with the two numbers either side, and its title.
Fifteen of the sixteen numbered entries met that test outright; the
sixteenth, *To-morrow is another day*, has its own number misread as
*(627*, and is fixed by its neighbours, its title and its registration. The
six without a number were found by title in the catalogue's own inverted
form — *Magic (The) of Maytime*, *Message (A) from the man in the moon* —
with the date and the composers agreeing. Five of the weakest were read on
the page image. `SRC0263`, rejected earlier on a title alone, is now placed
by its number on the right song.

Reading the scans corrected two citations. `SRC0257` gave the registration
as *E unp. 138678*; the catalogue prints *136678*, between 136386 and 136737
on the same page, and the citation and identifier now say so. `SRC0259` left
the number blank, and its note called it illegible in the digitized volume;
it is clear on the scan, *E unp. 137471*, and only the machine-read text
garbles it. All 89 entries now open on their page, which
`tests/test_copyright_catalogue_page_links.py` holds.

**Hofmeister: all 57 moved to the Internet Archive and open on their
page.** ANNO resets every connection from cloud hosts; the session's own
proxy passed the connection, and the Austrian National Library closed it,
so no network setting could help. The Internet Archive holds every yearly
volume from 1929 to 1933, and the entries now cite it, after the pattern
`SRC0869` already set: the scan as `primaryUrl`, *Internet Archive scan,
leaf nNNN* closing the citation, the Internet Archive as repository, and the
ANNO issue kept beside it as `alternate_access`, so the provenance is not
lost. Each scan was found by the entry's title and accepted only on the scan
the citation's own page number points to. For 1930–1933 that is the printed
page less one, in 52 entries; the 1929 volume is missing scans, the offset
growing from one in May to twenty-five by page 287, so its three entries
were read on the scan image. Two more were read the same way, and two whose
record title adds a word the register does not print. The four entries that
cite a second monthly issue had that link moved too; one of them, *Ich weiß
ein kleines Café* on page 106, the OCR reads as *Cafe* and the search misses,
and the image confirms it. `tests/test_hofmeister_page_links.py` holds the
move.

## 2. No link is dead; 131 could not be confirmed from here

| Result | URLs |
| --- | --- |
| Reachable | 646 |
| YouTube, confirmed to exist through its oEmbed service | 67 |
| YouTube, private or with embedding disabled (oEmbed 401) | 9 |
| Refused to automated requests (403, 429) | 73 |
| Connection reset at the TLS handshake | 44 |
| Server certificate fails verification | 4 |
| Server error (503) | 1 |
| **Dead (404, 410)** | **0** |

Of 844 URLs, 713 were confirmed working and none returned *not found*.

The 131 unconfirmed are a limit of this environment, not of the links. The
73 refusals are bot protection on Gallica (18), the Library of Congress (18),
Newspapers.com (8), Discogs, the California Digital Newspaper Collection and
others; they were not retried with a browser's identity, because that would
be circumventing the protection. The 44 resets include 37 ANNO pages and two
`web.archive.org` captures, and the Wayback Machine is certainly up, so a
reset here says nothing about the page. The four certificate failures
(`bcul.lib.uni.lodz.pl` twice, `mbc.cyfrowemazowsze.pl`,
`www.mmmrecordings.com`) were not diagnosed further; a browser may well open
them.

The nine YouTube 401s are the one group worth a look by hand: oEmbed answers
401 both for a private video and for one whose owner has disabled embedding,
and only a browser tells the two apart. *Checked:* all nine play in a
browser, so their owners have only disabled embedding, and the links stand.

## 3. A few records rest on Wikipedia alone, and one has a better Source in hand

No Work, Person, Place or timeline event rests on Wikipedia alone, and no
Wikipedia article is rated `high`. Nine records do:

- **`ORG128` Carl Lindström AG** cites only the German article on Otto
  Dobrindt. `SRC0725`, rated `high`, describes an Odeon label that prints
  “Carl Lindström A.-G.”, which is first-hand evidence for the Odeon–Lindström
  relation `ORG128` exists to carry. It is already in the dataset and does not
  link `ORG128`.
- **`ORG167` Gaumont British** and its two credits on F057 *My Song for You*,
  the director Maurice Elvey (`CON-F057-D-P204`) and the production company
  (`CON-F057-PC-ORG167`), all rest on the English article on the film
  (`SRC0889`). A filmographic database would do better.
- **Three Media**: the lobby cards `M038` *San Francisco* and `M076` *Three
  Smart Girls*, and the portrait `M254` Harold Adamson, the last on a source
  rated `low`.
- **Two name variants**: `PNV0044` Henri Eugène Vantard, the birth name of
  Henri Varna, and `PNV0065` Eddie Saxon, a pseudonym of Otto Dobrindt.

**Six of the nine now have a better Source beside the article.**

- `ORG167` Gaumont British and both F057 credits cite the *Kinematograph Year
  Book 1935* (`SRC0962`), whose page 302 lists the studio's productions with
  *My Song for You* and its director Maurice Elvey. The scan is linked at its
  page on the Internet Archive.
- `PNV0044` cites the BnF catalogue record of Henri Varna (`SRC0960`), which
  gives the birth name Vantard. The record was removed once, as `SRC0590`,
  because it only repeated the BnF badge; it now carries the name variant,
  which the badge cannot, and the badge links the catalogue record it cites.
- `PNV0064` and `PNV0065` cite the Library of Congress record of Otto
  Dobrindt (`SRC0961`). It does not list *Eddie Saxon* among its own
  references; it cites a 2008 BnF catalogue entry that gave the name as one,
  and the current BnF record no longer does, so the research note says so
  rather than claim more.
- `M254` Harold Adamson cites his profile at the Songwriters Hall of Fame
  (`SRC0963`, a new repository `ORG242`), which shows the same photograph. Its
  copy has the background cut away and ours does not, so it is not where the
  reproduction came from, and the note says that too. A portrait with two
  Sources had hidden the second one: the disclosure under the picture links
  only the first, and the person's own list left out every Source of the
  portrait. The list now leaves out only the one the disclosure shows.

The lobby cards `M038` *San Francisco* and `M076` *Three Smart Girls* stay
on Wikipedia. Where the reproductions came from is not recorded, and the
Wikimedia file pages that would say were refused to this environment
(HTTP 429). A reader with a browser can follow the article to the file page.

*Since traced.* A reverse image search, run in a browser, found both. The
*San Francisco* card is the Wikimedia Commons file *San Francisco lobby card
4.jpg*, at the same 744 × 580 pixels as the local copy (`SRC0965`); Commons
offers it as public domain for want of a notice, which the unread microtype
on the card leaves unconfirmed. The *Three Smart Girls* card is the one Alamy
offers from the Everett Collection (`SRC0966`, with new Organization records
for both); the agency calls it a handout or public-domain image, but the card
prints a 1936 copyright notice, so that is not adopted. Both cards now cite
these first and name them in their credit lines; the articles stay as film
context, and the rights status of both stays undetermined.

Nine Works rest only on sources rated `medium`. Five rest on the Walter
Jurmann society's website, alone or with an IMDb soundtrack entry:
W-S127 *Hi-do-ho*, W-S128 *Love Needs No Inspiration*, W-S165 *Magic*,
W-S166 *Rhumba* and W-S167 *Tahiti*. The other four are W-O010 *Parade de
France*, W-S183 *Diese Melodie sing ich nur für Sie*, W-S216 *Może tak, może
nie* and W-S218 *San Francisco*, the last on a YouTube upload.

**Of the nine, two now cite a national-library record, and one turned up a
conflict.**

- W-S216 *Może tak, może nie* cites the Biblioteka Narodowa record of the
  same Columbia DM 1624 disc (`SRC0964`), which enters Tuwim for the words
  — printed on the label as Oldlen — and Kaper for the music. It dates the
  disc *[ca 1935]* where Stare Melodie gives 1932, and the note keeps the two
  apart.
- W-O010 *Parade de France* was never as thin as it looked. Each of its four
  songs has its own BnF notice, rated `high`, that names the revue, but the
  revue and the four song-to-revue relations cited only the collective
  notice. They now cite the song notices too. The revue's own credits still
  rest on the collective notice, since the song notices do not say who wrote
  the revue's music as a whole.
- W-S218, the Polish *San Francisco*, credits the words to Emanuel Schlechter
  on a YouTube upload alone, and its version relation is marked `confirmed`.
  The Biblioteka Narodowa knows two Odeon pressings of a Polish *San
  Francisco*, both with words by **Zenon Friedwald** and sung by Albert
  Harris, and no Syrena issue and no Schlechter text. The two may be
  different texts; the upload cannot be listened to from here. The version
  relation, the last part still marked `confirmed`, is now `probable` like
  the credits, and the Schlechter credit and the relation say why.
- The other six found nothing better. *Hi-do-ho* and *Love Needs No
  Inspiration* are not in the copyright catalogues for 1935 or 1936, nor
  *Magic*, *Rhumba* and *Tahiti* in 1937, which fits the Jurmann
  catalogue's account of them as songs for films; *Diese Melodie sing ich
  nur für Sie* is not in Hofmeister for 1931 or 1932.

`P206` Serge Veber has no `sourceIds` of his own, and that is consistent
rather than missing. His one credit, the film lyrics of *Ninon*, rests on
`SRC0298` and `SRC0584`, and so do the credits of his co-authors Henri-Georges
Clouzot and Charles-Louis Pothier on the same song, neither of whom those
Sources list either. A Person's `sourceIds` hold the Sources about the
person, not those behind the person's credits, and none in the dataset is
about Veber. Linking him alone would have broken the pattern for the other
two.

## 4. `http://` is on 25 Sources, not 9

The earlier count looked at `primaryUrl` and `accessUrl` only;
`additionalLinks` holds the rest.

| Host | Fields | `https://` |
| --- | --- | --- |
| `musiktiteldb.de` | 8 primary, 10 additional | certificate invalid; keep `http://` |
| `www.kppg.waw.pl` | 1 primary, 4 additional | certificate invalid; keep `http://` |
| `discography.phonomuseum.at` | 1 additional (`SRC0583`) | serves the byte-identical PDF; switch |
| `cinema.encyclopedie.personnalites.bifi.fr` | 1 additional (`SRC0667`) | not reachable from here either way |

## 5. Smaller items

- **Record identifiers in research notes.** 26 notes refer to 32 other
  records by identifier, `SRC0758` or `M060`, as plain text. Source numbers
  are printed on every card, so a reader can search for one, but cannot
  click it. Linking them in the renderer, or naming the document in words as
  `evidenceLocator` now does, would fix it.

  **Done in the renderer.** Three note fields reach a page — a Source's
  research note, a credit's note and a film's attribution note — and they
  hold more identifiers than the 32 counted here: 66 notes in all. Each
  identifier of a record with a page (Source, Media, Person, Organization,
  Work) is now a link to it. An identifier joined to a hyphen is left alone,
  so the matrix number *M519-1* stays text. The six song numbers in three film
  notes (`S053` and the like) became their Work's identifier, and two credit
  notes that named a name-variant record, which has no page, now say in words
  where the pseudonym is documented. `tests/test_note_record_links.py` checks
  that every linked identifier exists and that none without a page is left.
  That check found one that did not exist: the note on *Two Hearts in Wax
  Time* cited `SRC0401` for Edward Ward as a music-department credit, a
  Source that was never in the public data. Nothing else in the dataset ties
  Ward to the film, and IMDb's credits could not be read from here, so the
  sentence was removed; it can return with a Source.
- **DOI not in `identifiers`.** `SRC0443`, `SRC0684` and `SRC0792` link
  through `doi.org` and do not carry the DOI as an identifier, so it is not
  printed on the card as every other DOI is.
- **No repository.** `SRC0864`, Krasnoborski's 1975 interview reproduced on
  the Cinescores Center site, names none. The other three Sources without one
  are the Buxbaum book, which now carries its ISBN, and the two forthcoming
  Lindstedt articles. *Done:* the site is now its repository, as a new
  Organization record, and the citation adds what the page itself says,
  that the text is reproduced by permission of the magazine's editor, Luc
  Van de Ven.
- **An access date with nothing to access.** `SRC0789`, the *Cocktails* cover
  examined in a research reproduction, has no link but an `accessDate`, which
  the card prints as *Accessed*. *Done:* the date is when the reproduction
  was read, so it stays, and a Source with no link at all now prints it as
  *Consulted*.

## Checked and found sound

- **No duplicates.** No two Sources share a full citation or a title. The 38
  URLs shared by several Sources are catalogue volumes and issues holding
  several entries. The two pairs that looked like one document twice are two:
  `SRC0037` and `SRC0566` share a NARA file unit but are different pages and
  different people, and `SRC0045` and `SRC0046` are a notice and an
  advertisement on the same page of *Variety*.
- **Dates.** None lies in the future, none follows its own access date, every
  access date is well formed, and every linked Source has one.
- **Public text.** No working notes, stray whitespace, URLs inside citations
  or straight quotes in titles and citations.
- **Reliability.** No Wikipedia article is rated `high`, and every Source
  marked `verified_with_attribution_note` carries its note.
- **ARK identifiers.** Every ARK in a URL is also recorded as an identifier.
- **Orphans.** The three Sources that link no Work, Person or Media —
  `SRC0853` on the Alberti firm and the two register records `SRC0931` and
  `SRC0932` — document an Organization, which is what they are for.
- **False leads.** 37 “double full stops” are the three-dot ellipses of
  printed titles such as *Ninon... quand tu me souris*. “M519” in `SRC0008`
  is a matrix number, M519-1, not a Media record.

## Suggested order of work

1. ~~Link `ORG128` to `SRC0725` (finding 3).~~ Done: Carl Lindström AG now
   cites the Odeon label that prints its name, beside the Wikipedia article.
2. ~~The three DOIs and the phonomuseum `https://` switch (findings 4–5).~~
   Done. Each DOI was confirmed at `doi.org` to resolve to the record the
   Source already describes, and is now printed on the card. The `https://`
   link had to be changed in `scripts/recording_sources.py`, which pins that
   Source's fields; the normalizer otherwise put `http://` back. Serge
   Veber's Sources were left as they are, for the reason given under
   finding 3.
3. Deep links for the 57 Hofmeister and 85 copyright-catalogue entries
   (finding 1). ~~Copyright catalogue~~ done for all 89: 63 by
   registration and title, the last 22 by entry number and title. ~~Hofmeister~~ done: all 57 moved to the
   Internet Archive scan, with ANNO kept as alternate access.
4. ~~Replace or reinforce the Wikipedia-only Sources for Gaumont British, its
   two F057 credits, the three Media and the two name variants (finding 3).~~
   Done for all but the two lobby cards, whose provenance could not be
   reached from here.
5. ~~Check the nine YouTube 401s in a browser (finding 2).~~ Done: all nine play.
6. ~~Link or reword the record identifiers in research notes (finding 5).~~
   Done, in the renderer, for every note a page prints.
