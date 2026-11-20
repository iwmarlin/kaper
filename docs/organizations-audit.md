# Organizations audit, 20 November 2026

The 243 Organization records were checked in four ways:

- the records themselves, for duplicates, missing fields and links;
- the 71 GND identifiers, each resolved through lobid.org and compared with
  the record's name and place;
- the production companies of the 27 films linked to filmportal.de,
  compared with filmportal's “Produktionsfirma”;
- every credit that names an organization, compared with the Sources it
  cites.

There are no duplicate records. The records without an authorized-name
source are websites, which carry their own names as local headings.

## Corrected

### Records

- **`ORG029` Wiener Bohème Verlag.**
  - The display name lacked its accent.
  - The record gave only Vienna, but the house also had a Berlin branch.
  - The GND record (1064328784) gives the history, which the note now
    states. The house was founded in Vienna on 1 November 1919 by Otto
    Hein. Ufa bought the Berlin branch on 19 December 1931 and renamed it
    the Wiener Bohème Verlag G.m.b.H. After 1932 it was a wholly owned Ufa
    subsidiary.
- **`ORG031` Edition Karl Brüll.** The note said that no GND record
  existed. GND 107295706X (VIAF 311832467) is Edition Karl Brüll (Berliner
  Bohème-Verlag), owned by Karl Brüll from 1922. It succeeded the Berliner
  Bohème-Verlag, Inh. Karl Brüll. The record now carries both identifiers
  and takes its heading from them. Whether the owner is the lyricist Karl
  Brüll (`P114`) is not established, and the note says so.
- **`ORG010` Emelka-Konzern.** The name variants now include Münchener
  Lichtspielkunst AG, the company's GND heading.

### Credits

- **`W-S009` “Tränen weint jede Frau so gern”, Alrobi.**
  - The publisher credit cited Hofmeister for December 1929, p. 287.
    That entry is an arrangement for band published by Seifert of
    Eppendorf.
  - The Alrobi edition is listed in March 1929, p. 65 (leaf n64), which is
    now `SRC1023`.
- **`W-S026` “Ich hab’ heut’ grad’ Geburtstag”.**
  - The song was credited to the Drei Masken Verlag.
  - Both of its Sources name Alrobi instead: GEMA work 1869745-001 gives
    Alrobi Musikverlag as original publisher, and the 1930 copyright entry
    gives Alrobi Musikverlag G.m.b.H., Berlin.
  - The credit is now Alrobi's (`CON-S026-PUB-ORG033`).
- **`ORG007` Maxim-Film GmbH, withdrawn.**
  - It was credited as a producer of *Ihre Majestät die Liebe* on
    filmportal's authority. Filmportal names only the Joe May-Film A.-G.
  - None of the film's other Sources, nor the programme cover `M175`,
    names Maxim-Film.
  - The credit and the record are withdrawn, and the record's address
    leads to the film.
- **Two production credits resting on Sieghardt alone are now `probable`:**
  - the Société Internationale Cinématographique for *Voyage de noces*,
    for which filmportal names no company;
  - Cinéproduction for *Un coup de rouge*.

### Links

Organizations had not been linked to Places. Five links are now recorded:

| Organization | Place |
|---|---|
| `ORG001` MGM | `PL006` MGM Studios |
| `ORG039` Salabert | `PL021` Salabert studio |
| `ORG011` Ufa | `PL031` Babelsberg |
| `ORG011` Ufa | `PL020` Ufa-Theater Universum |
| `ORG111` Teatr “Perskie Oko” | `PL046` Perskie Oko |

The theatre is also linked to `TE0014`, the 1926 songs it introduced. Until
now it had no link at all.

## Checked and found sound

- **GND.** Every other identifier resolves to the organization named, at
  the place the record gives.
- **Filmportal.** 25 of the 27 films agree with filmportal on their
  production companies. The other two:
  - *Ihre Majestät die Liebe*: filmportal confirms the Joe May-Film A.-G.
    but not Maxim-Film, which is withdrawn as described above.
  - *Voyage de noces*: filmportal names no company. Its credit to Mondial
    agrees with the U.S. Commerce Department's *European Motion-Picture
    Industry in 1932* (1933). That report has Mondial of Vienna producing
    one German film in 1932 “and also … a French version”. The report
    does not name the film, so the citation is not added as item-level
    evidence.
- **Wiener Bohème Verlag** is the same entity as the GND heading, whose
  later dates (1947 and after) belong to the post-war Berlin house.

## Open

- **`W-S013`, Edition Meisel.** The song's two publisher credits, Alrobi
  and Edition Meisel & Co., cite the Deutsches Lied index of *1000 Takte
  Tanz*, Band 2. Hofmeister (1929, 1930) lists that album series as
  Alrobi's, which supports the Alrobi credit. The index record that would
  show Meisel cannot be opened automatically, so the Meisel credit is left
  as it stands.
- **UniFrance.** The French production credits that cite UniFrance (Films
  R.P., Vandor-Film, and SIC for *Le greluchon délicat*) could not be
  re-read. The site blocks automated access.
- **The Seifert band arrangement** of “Tränen weint jede Frau so gern” is
  recorded in `SRC0103` but has no publisher credit of its own.
