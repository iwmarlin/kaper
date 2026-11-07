# People and organizations audit, 7 November 2026

A close review of the 179 People and 238 Organizations, read the way an
authority file is read: is each heading the one its register gives, does
each identifier lead to the right person or body, do life dates agree with
the registers, and do the credits that rest on an organization say what
their Sources say.

**Method.** Every register identifier the records link was read through the
register's own machine-readable service: 149 LCNAF records through
`id.loc.gov`, 90 GND records through `lobid.org`, 34 BnF records through
the BnF SRU service, and 58 Wikidata items. That is 331 of the 350
identifiers that can supply a heading or a date. BnF, which did not answer
during the September heading review, answered this time, so the people that
review left open could be settled. People with no BnF link were also
searched in BnF by name and life dates. The Polish national library (BN)
could not be read: its certificate has expired, and the check was not
bypassed.

## Outcome

Findings 1 to 5 were corrected on 7 November 2026, with
`tests/test_people_audit_fixes.py` holding them in place.

- The 22 credits are now `copyright_claimant` credits for the firm each
  entry names, with their identifiers changed to match (`CON-S122-CC-ORG001`
  and so on), and the songs no longer carry the claimant in their publisher
  field. Neither the Jurmann catalogue nor the Brooklyn notice names a
  publisher, so they no longer support those credits. Robbins was at first
  kept as the publisher of *Keep the Magic of Springtime* on Sieghardt's
  catalogue; read in the book, the entry (p. 214) says only “Nicht
  verwendet” and names no publisher, so that credit was removed too.
- The eleven headings follow the language-area register, and the BnF and
  GND records they come from are linked. Sig Arno's GND record is linked as
  well.
- **Max Kolpe** is headed *Colpet, Max*, as the GND gives it, and as the
  archive already does for Ben Berlin. The page keeps *Max Kolpe*, the name
  his credits print. A new name variant, *Max Colpet*, records the later
  form with its evidence (the LexM entry and the portrait article), so
  that the heading is not a puzzle to a reader.
- Bonnal links his own BnF record. The Library of Congress source on his
  pseudonym had said the BnF record it cites was Bonnal's; it was the
  pseudonym's, and the note now says so. France-Mélodie lost its Dewey
  link, and France-Mélodie, Éditions musicales universelles and Universal
  Music Corporation are marked as local headings. Wohlmuth and Éditions Coda
  link their BnF records, and Coda takes BnF's heading, *Éditions Coda et
  Max*.
- Eddy Duchin's and H. André Legrand's life dates are `disputed`, each with
  a note and the register record that disagrees (`SRC0968`, `SRC0969`).
  BnF's coded data for Legrand gives his death as 15 August 1885, before
  his birth, evidently a keying error for 1985.

### Second pass, the same day

The three items left open were settled once BN answered again.

- **Polish headings.** BN gives *Kaper, Bronisław (1902–1983)* and *Gold,
  Henryk (1899–1977)*, which become the headings, with the BN records
  linked. BN and BnF disagree on Gold's birth year, 1899 against 1902, so
  his dates are `disputed`, with the BN record as `SRC0971`. Andrzej Włast,
  Jan Kiepura, Józef Śmidowicz, Julian Tuwim and Jerzy Fitelberg have the
  same heading in BN as in the archive. Their heading source is now BN, the
  register of their language area, and the BN records are linked.
- **Qualifiers.** The archive already kept a register's qualifiers wherever
  it transcribed a heading: *Gold, Henry (Composer)*, *Connelly, Reg.
  (Reginald)*, *Samuels, Walter G. (Walter Gerald)*. Louis B. Mayer was the
  one exception. `docs/authority-headings.md` now says so: only dates are
  stripped, and every other qualifier stays, for organizations as for people.
  Mayer is headed *Mayer, Louis B. (Louis Burt)* from LCNAF, the register of
  his language area, and Gaumont British *Gaumont British Picture Corp.*,
  as LCNAF gives it. Syrena Record is in BN as *Syrena Record*, which is
  the archive's heading, so no qualifier arises and its source is now BN.
- **Constantin Landau.** The BnF record *Lândau, Konstantin Ûlianovič
  (1890–1969)* names *Madame ne veut pas d’enfants* among its associated
  forms, the film the archive credits him with directing, so the identity
  rests on the register itself. The record is linked and cited
  (`SRC0970`), and his life dates are 1890–1969. His heading stays the
  GND's *Landau, Constantin*: the rule names no register for Russian, and
  GND is the first in the general order that holds him.

Nothing from this audit is left open.

## 1. Twenty-two publisher credits rest on unpublished registrations

The Catalog of Copyright Entries names the **copyright claimant** after the
registration number; its own note says so (“If the claimant of copyright is
the same as the author of words or music, no statement of authorship is
given”). For an *E pub.* entry the claimant of a music firm's song is
usually its publisher. For an *E unp.* entry nothing was published, and
the name is the claimant alone. The works audit applied this to four
songs; the same reading was not applied to their credits.

| Credits | Claimant in the entry | Now credited as |
| --- | --- | --- |
| 19 songs, e.g. *Shadows on the Starlit Waters*, *Alma Mater*, *Be Mine*, *Never Was There Ever Such a Perfect Day* | Metro-Goldwyn-Mayer Corp. | publisher: MGM |
| *Someone to Care for Me* | Leo Feist, Inc. | publisher: Feist |
| *Beyond My Fondest Dreams* | **Metro-Goldwyn-Mayer Corp.** | publisher: **Robbins** |
| *Keep the Magic of Springtime* | **Metro-Goldwyn-Mayer Corp.** | publisher: **Robbins** |

The last two are wrong twice over: the entry names MGM, not Robbins, and
says the song was unpublished. *Keep the Magic of Springtime* has a second
Source, Sieghardt's catalogue, which may name Robbins; *Beyond My Fondest
Dreams* has none.

**Fix.** Each becomes a `copyright_claimant` credit for the firm the entry
names, as was done for *The Magic of Maytime*. A publisher credit stays
only where another Source names a publisher. Three of the songs have
other Sources: the Jurmann catalogue, a Brooklyn newspaper notice and
Sieghardt's catalogue. Each is read for a publisher before a credit is
changed.

## 2. The language-area rule was not applied to headings taken from LCNAF

Since 25 September, `docs/authority-headings.md` puts the register of a
person's own language area first: GND for German, BnF for French, BN for
Polish, LCNAF for English. The September review applied it only where the
archive's heading already differed from LCNAF. Headings transcribed from
LCNAF were never re-read against the language-area register, and eleven
differ.

**French language area (BnF)**

| Person | Heading now (LCNAF) | BnF | Note |
| --- | --- | --- | --- |
| `P010` Ch.-L. Pothier | Pothier, Charles Louis | **Pothier, Charles-Louis** | BnF not linked |
| `P032` Henri-André Legrand | Legrand, H. André (Henri-André) | **Legrand, H. André** | BnF not linked; BnF gives 1896–**1985**, LCNAF and GND 1986 |
| `P033` Henri-Georges Clouzot | Clouzot, H.-G. (Henri-Georges) | **Clouzot, Henri-Georges** | BnF not linked |
| `P072` Roger Féral | Féral, Roger | **Feral, Roger** | BnF not linked; BnF sets the name without the accent |
| `P109` Henri Lemarchand | Lemarchand, Henry (GND) | **Lemarchand, Henri** | BnF not linked; this was the September review's open case |
| `P111` Joseph-Ermend Bonnal | Bonnal, Ermend | **Ermend-Bonnal** | The BnF record linked is the one for his pseudonym, *Marylis, Guy*; his own is `cb14793454j` |

**German language area (GND)**

| Person | Heading now (LCNAF) | GND | Note |
| --- | --- | --- | --- |
| `P056` Max Ophüls | Ophuls, Max | **Ophüls, Max** | GND not linked (`11859009X`) |
| `P148` Helmut Wolfes | Wolfes, Helmuth | **Wolfes, Helmut** | |
| `P152` Stefan Weiß | Weiss, Stephen | **Weiss, Stephan** | The Viennese composer; LCNAF has the American form he used later |
| `P205` Dajos Béla | Dajos, Bela (BnF) | **Dajos, Béla** | The record follows BnF, which drops the accent; GND and LCNAF agree on *Béla* |
| `P054` Max Kolpe | Kolpe, Max | **Colpet, Max** | GND files him under the name he took in exile. The archive did the same for Ben Berlin (`P130`), whom GND files under his stage name. |

**Polish language area (BN), not checkable.** `P009` Bronisław Kaper is
headed `Kaper, Bronislaw` from LCNAF, without the diacritic that BnF and
every Polish Source print. `P119` Henryk Gold is `Gold, Henry (Composer)`.
If BN holds them, as is likely, its headings come first; this waits until
BN can be read.

Two cases where the person's language area is a judgement were left
alone: Alexis Granovsky, a Russian-born director working in Paris, and
Josephine Baker, an American who became a French citizen in 1937.

## 3. Identifiers that lead somewhere else

- **`ORG048` France-Mélodie** links BnF `cb14605880n`, which is a Dewey
  classification record (“Chansons classiques occidentales – France”), not
  the publisher. BnF holds no authority record for France-Mélodie, so the
  heading is the archive's own and should be marked as local.
- **`P111` Bonnal**, above: the pseudonym's record is linked in place of
  his own.

## 4. Headings that name a register without linking it

`docs/authority-headings.md` asks that a heading's register be linked, “a
heading that names a register the record does not link is a claim nobody
can check”. Three records name BnF and link nothing:

- **`P069` Robert Wohlmuth.** BnF holds him: *Wohlmuth, Robert, 1902–1987*,
  cinéaste, `cb17166302h`. Heading and dates agree; only the link is
  missing.
- **`ORG030` Éditions Coda.** BnF holds *Éditions Coda et Max*, music
  publisher, 12 rue Lafayette, Paris, with *Éditions Coda* as a variant and
  a publisher's catalogue of 1934–1935 as its Source. The archive's own
  sheet music prints “EDITIONS CODA S. A., 12 rue Lafayette, Paris”, so this
  is the same firm, and BnF's heading is *Éditions Coda et Max*.
- **`ORG032` Éditions musicales universelles.** BnF holds no authority record
  under this name or any part of it. The heading cannot have come from a BnF
  authority; it should be marked as local.

`ORG246` Universal Music Corporation, added in the works audit, records no
heading source. No register holds it; it should be marked as local too.

## 5. Life dates

Registers agree with the record for every person except these. Where the
cited registers conflict, the archive marks the dates `disputed` and
explains them; nine people are already so marked.

- **`P133` Eddy Duchin** is `confirmed` 1909–1951, while the GND record it
  links gives 1910. That is the same conflict as Jeanette MacDonald's and
  Paul Kohner's, which are marked `disputed` with a note.
- **`P032` Henri-André Legrand**: if BnF is linked, its 1985 against 1986
  in LCNAF and GND becomes a conflict of the same kind.
- **`P011` Constantin Landau** has no life dates. BnF has *Lândau,
  Konstantin Ûlianovič, 1890–1969*, poet, stage and film director, with
  *Landau, Constantin* as a variant. It is very likely the same man, but no
  Source the archive holds ties the director of *Coup de feu à l’aube* to
  him, so it is noted, not applied.

Wikidata gives another birth year for Ben Berlin (1896), Georg Jacoby,
Paul Kohner and Ralph Benatzky, but Wikidata is not a register under the
archive's rules, and the registers agree with the record.

## 6. Smaller items

- **Two organization headings differ from LCNAF.** `ORG167` is headed
  *Gaumont-British Picture Corporation*; LCNAF gives *Gaumont British
  Picture Corp.* `ORG132` drops LCNAF's qualifier: *Syrena Record* for
  *Syrena Record (Firm)*. As a Polish firm, its BN heading should come
  first, and BN cannot be read. The rules say nothing about qualifiers or
  about organizations, which is the same question as Louis B. Mayer's
  *(Louis Burt)*, still open since September.
- **Registers available but not linked.** Sig Arno is in GND as *Arno,
  Sig*, the same heading, so only the link is missing.
- **Split clusters.** For Erich Schmidt, René Pujol and Emanuel Schlechter
  the GND record points to a different VIAF cluster from the one the
  record links, and Jean Féline has two ISNIs. VIAF and ISNI are hubs, and
  these are their duplicates, not the archive's.

## Checked and found sound

- **Identity.** Every LCNAF, GND, BnF and Wikidata record linked is the
  person or body named, apart from the two in finding 3. The GND, LCNAF and
  Wikidata identifiers on each record point at one another wherever more
  than one is linked; the National Film Institute Hungary's GND record points
  at the LCNAF record of its predecessor, the Hungarian National Film Fund,
  which is a register's history, not an error.
- **Headings** taken from the register they name match it, character for
  character, apart from the cases above. That covers 133 LCNAF, 16 GND
  and 13 BnF headings; the four BN headings could not be read.
- **The September open cases** are settled, apart from Ferry van Delden
  (VIAF still behind a bot check) and Karl Brüll (no GND record). Ninon
  Steinhoff, Charlie Davson, Didier Mauprey, Karl Michael May and Georges
  Rey match their BnF records.
- **Roles.** A person's roles describe their occupations, not their
  credits, and every credit is consistent with them. Ten people have no
  credits and are in the archive for Kaper's life: his teachers, his
  sister, Mayer, Laemmle, Kohner and Lubitsch. Each is tied to a timeline
  event.
- **Pseudonyms** are recorded as name variants with their evidence: Jean
  Cis for Francis Salabert, Marylis for Ermend-Bonnal, Ben Berlin and
  Hermann Bick for Hermann Biek.
- **Organizations.** None is a duplicate of another, and every credited
  organization has a type that fits its credits. MGM's publisher credits
  are dealt with in finding 1.

## Order of work

All five items are done.


1. Turn the 22 credits on unpublished registrations into claimant credits,
   and correct the two that name Robbins (finding 1).
2. Apply the language-area rule to the eleven French and German headings,
   linking the BnF and GND records (finding 2).
3. Replace Bonnal's BnF link, remove France-Mélodie's, and link Wohlmuth
   and Éditions Coda. Mark France-Mélodie, Éditions musicales universelles
   and Universal Music Corporation as local headings (findings 3 and 4).
4. Mark Eddy Duchin's dates `disputed` with a note, and Legrand's if BnF is
   linked (finding 5).
5. Decide the qualifier question (Mayer, Syrena, Gaumont), and check the
   two Polish headings once BN can be read.
