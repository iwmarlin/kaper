# Works audit, 7 November 2026

A second, closer review of the 300 Works — 214 songs, 56 films and 30 other
works — read as a thematic catalogue is read: is each title the one the
documents print, is each work one work, are its versions, credits, film and
dates consistent. Every candidate a script raised was read against its
Sources before it was kept; those that did not survive are listed at the end.

## Outcome

Findings 1 to 4 were corrected on 7 November 2026, with
`tests/test_works_audit_fixes.py` holding the corrections in place. Reading
the Sources again for the fix overturned two of the findings below, and they
were left as they were:

- **`W-S001`** keeps *A zresztą niech pan do mnie zadzwoni*. The sheet
  music itself (SRC0067) prints *do mnie*; the catalogue and the upload
  shorten it.
- **The two Polish versions** are correctly not linked to *Ein Lied für
  Dich*. A version is linked to a film only when it was sung in it, and the
  Polish words were not; they name the film's Polish release title only as
  the source of the tune.

One fix of finding 3 was also withdrawn: *Pourvu qu’on ait vingt ans* keeps
Éditions Echo as printed with no publisher credit, following the earlier
reviewed decision on recording-label publishers.

Stronger evidence than the audit cited was found for two titles: the
1930 sheet music (SRC0379) prints *O tem wróble świergocą...*, and the Robbins
sheet music in the USC collection (SRC0535) prints *Cosi Cosa*. *Oh Madonna!* follows
the 1933 Odeon label; the register's *O Madonna* is kept as a variant.

*Two Hearts in Wax Time*: the copyright entry (SRC0967, LP5806) lists no
credits, and the trade papers of 1935–1938 that list and review the short
name no director. That was first recorded as “no Source names one”, which
was wrong: Sieghardt's filmography of Walter Jurmann, already among the
film's Sources, names Earl Haley and Maurice Kusell (p. 224, entry 40). They
are now its directors, `probable` because that one secondary Source is all
that names them, and the film's note says who gives what.

*Sous le ciel de Venise*: Sieghardt's opus list (p. 198) prints the French
version both ways, *Sous le ciel de Venise* in the entry for op. 128 and
*Sous le ciel de Venice* in its own entry, op. 128/F. The record now takes
the French form and keeps *Venice* as a variant. Both the French and the
German version are dated 1936, as the catalogue dates them and as their
original is dated; they had been 1937. Nothing from this audit is left
open.

## 1. Eighteen titles are not the form any Source prints

A Work's title should be the form its earliest primary Source prints, with
English titles set in headline case and period spelling kept, as the
archive does for almost every work. These are not.

**Words no Source prints**

| Work | Record title | Printed |
| --- | --- | --- |
| `W-S001` | A zresztą niech pan **do mnie** zadzwoni | *A zresztą, niech pan zadzwoni!* (KPPG catalogue); *A zresztą… niech pan zadzwoni.* (upload) |
| `W-S022` | O **tym już** wróble świergocą na dachu | *O tem wróble świergocą* (1930 advertisement); the Biblioteka Narodowa holds the 1930 print as *O tem wróble świergocą…* and a disc as *O tem wróble świergocą na dachu*. *O tym już…* is a modern transcription on Stare Melodie. |
| `W-S078` | O Madonna**, komm zu mir** | *O Madonna* (AKM register); *Oh Madonna!* (Odeon O-4707, 1933). The added words belong to *Signorina! komm zu mir*, from the same film. |
| `W-S092` | Ich geh’ nie von Dir fort**, denn ich lieb’ Dich!** | *Ich geh nie von dir fort* (Hofmeister, 1933); *Ich geh’ nie von dir fort* (discography) |
| `W-S156` | Never Was There Such a Perfect Day | *Never was there **ever** such a perfect day* (copyright registration, 1937), its only Source |

**Punctuation or spelling no Source prints**

| Work | Record title | Printed |
| --- | --- | --- |
| `W-S002` | Jak się da, to się zrobi | *Jak się da, to się zrobi!* |
| `W-S003` | Zgaś lampę | *Zgaś lampę!* |
| `W-S068` | Signorina, Signorina, komm zu mir | *Signorina! komm zu mir* (Hofmeister, 1933) |
| `W-S082` | In 24 Stunden kann soviel gescheh’n | *In 24 Stunden kann soviel geschehn* (Hofmeister, 1933) |
| `W-S086` | Kind, ich freu’ mich auf dein Kommen | *Kind, ich freu mich auf dein Kommen* (Hofmeister and the sheet music, its two Sources) |
| `W-S101` | Ganz Ihrer Meinung, **J**awohl | *Ganz Ihrer Meinung Jawohl* (GEMA, which sets every title in capitals) — *jawohl* takes no capital mid-title |
| `W-S107` | En **A**vant | *En avant* and *En avant !* (BnF) |
| `W-S112` | Vivons l’amour**!** Vivons la vie | *Vivons l’amour, vivons la vie* in every one of its Sources |
| `W-S118` | Così, cosa | *Cosi Cosa* in every Source of the time; *Così, cosa* only in a YouTube upload rated `low` |
| `W-S125` | Tillie, the Tight Rope Walker | *Tillie the tight rope walker* (both registrations) |
| `W-S157` | Swing, Mister Mendelssohn | *Swing Mister Mendelssohn* (both registrations); the comma only in an upload |
| `W-S172` | Goodnight | *Good-night* (registration), its only Source |
| `W-S191` | Mit dir möchte ich zieh’n bis zum Ende der Welt | *Mit dir möchte ich ziehn …* (Pfau), its only Source |

**Headline case.** `W-S212` *Penny’s return* and `W-S228` *Dairy-maid Song*
keep the lower case of the copyright catalogue, which sets every title so;
every other English title is in headline case — *Penny’s Return*,
*Dairy-Maid Song*.

**Not verifiable from here.** `W-S198` *Sous le ciel de Venice* rests on
Sieghardt's work catalogue alone. *Venice* is the English name; a French
title would read *Venise*. Worth checking in the book. *(Checked: see
Outcome.)*

The fix keeps each record's identifier, address and slug; only the title
and sort title change. Where a Source does print the old form — the
upload's *Così, cosa* and *Swing, Mister Mendelssohn*, the discography's
*Ich geh’ nie von dir fort* — it stays as a title variant, so a search for
it still finds the work. The Walter Jurmann catalogue, which prints *Never Was
There Such a Perfect Day*, was added to that work's Sources with the
variant.

## 2. Four French titles are both a variant of a German film and a film of their own

The French versions of four German films have their own records, and each
French title is also recorded as a title variant of the German film:

| French version (own record) | Also a variant of |
| --- | --- |
| `W-F020` *Madame ne veut pas d’enfants* | `W-F017` *Madame wünscht keine Kinder* |
| `W-F019` *L’Homme qui ne sait pas dire non* | `W-F022` *Ich will Dich Liebe lehren* |
| `W-F025` *Tout pour l’amour* | `W-F023` *Ein Lied für Dich* |
| `W-F027` *Le chant du destin* | `W-F026` *Abenteuer am Lido* |

A multiple-language version is a separate film, shot with its own cast, so
its title belongs to its own record. As variants of the German films the
titles make a search for *Tout pour l’amour* find two films. The variants
should go, unless a Source shows the German film itself released in France
under that title. The Polish *Zdobyć cię muszę* on *Ein Lied für Dich* is
different: there was no Polish version, and it is the German film's Polish
release title.

## 3. Publisher fields that hold something else

`publisherAsPrinted` on a song is meant for the firm that published it.

- **Claimants of unpublished registrations.** An *E unp.* entry has no
  publisher; the firm named is the copyright claimant. *My Heart Is a Gypsy*
  and *At Night* record Loew’s / MGM as claimant through a
  `copyright_claimant` credit, as they should. *The Magic of Maytime*
  (Metro-Goldwyn-Mayer), *Penny’s Return* and *New York* (Universal Music)
  hold the claimant in the publisher field with no credit; *Please Forgive
  Me* holds its two composers there, who were their own claimants.
- **A publisher without a credit.** *The Orchestra in Love* names Chappell &
  Co. and has no publisher credit.
- **A record company.** *Ninon, ach uśmiechnij się!* and *Signorina,
  signorina* hold the Odeon record company, already credited as their label.
- **“Manuscript.”** Five songs — *Hätt’ ich einen Kammerdiener?*, *Denkst du
  noch an jeden Tag*, *Magic*, *Rhumba*, *Tahiti* — hold the word
  *manuscript* or a holding statement; the holding credit says that already.
- *Pourvu qu’on ait vingt ans* names Éditions Echo, which its disc prints as
  publisher, and has no credit for it.

The fix moves claimants to `copyright_claimant` credits, adds the two
missing credits, and empties the field where it held something else.

## 4. Smaller items

- **Jurmann collaboration not marked on twelve songs** he is credited on —
  *Wir sind international*, *À Paris tiguidiguidi*, *At Night*, *Please
  Forgive Me*, *Blush and Sigh*, *Ninon*, *Adieu* (1935), *The Sweetest Song
  in All the World*, *The Magic of Maytime*, *Learn to Smile*, *Falling in
  Love with You*, *Signorina*. The site does not read the flag, but the data
  should agree with the credits.
- **One genre spelled apart.** *Just One of My Dreams* has *slow foxtrot*;
  the other 26 have *slow_fox*. Five songs have no genre, correctly: their
  registrations give none.
- **Instrumentation wording.** *Fiesta (Bianca)* is a transcription “for 2
  pianos”; the other Cocktails say “two pianos”.
- **`W-F039` *Two Hearts in Wax Time* has no director.** IMDb, its Source,
  could not be read from here. *(Sieghardt names two: see Outcome.)*
- **The two Polish versions are not linked to their film.** *Ninon, ach
  uśmiechnij się!* and *Signorina, signorina* name *Zdobyć cię muszę*, the
  Polish release title of *Ein Lied für Dich*, and are linked only to their
  German originals. *(Correct as it is: see Outcome.)*

## Checked and found sound

- **Identity.** No two Works are one work. The shared titles are different
  works: the film and the song *Es wird schon wieder besser* and *Kind, ich
  freu’ mich auf Dein Kommen*; the three *San Francisco*s (the film, the song,
  the Polish version); and two different songs called *Adieu*, the French one
  of 1933 from *Le chant du destin* and the English one of 1935 with words by
  Ned Washington.
- **Records agree.** Every Work's Song, Film or Other Work record carries the
  same title, year, period and certainty.
- **Years** follow the rule in `docs/work-years.md`; periods follow the years,
  1926 counting as Berlin for the songs written there.
- **Versions.** Every language version has the composers of its original,
  except where the record says why: the French *O chant d’amour de Tahiti !*
  adds Georges Rey, and the French versions of two films credit Kaper as
  music director rather than composer, as their Sources do.
- **Songs and films.** Every French song version that names a film is
  linked to the French film it was sung in, and the versions of the
  Hollywood songs name the film of their original.
- **Films.** Kaper's part on each film — composer, songwriter, music
  director, stock or background music — matches his credits. *Coup de feu à
  l’aube* has no stated part, and its note explains that no Source names
  him.
- **Series.** All eleven Cocktails and seven Jazz Drops are linked to their
  series.
- **French capitals** follow the Sources: *La Chanson du pays*, *La Femme aime
  à verser des larmes* and *L’Homme qui ne sait pas dire non* are printed so.
  *Le chant du destin* is printed both ways, and the record takes the film
  database's form.

## Order of work

All five items are done.

1. Correct the eighteen titles and the two English cases, keeping the old
   forms as variants where a Source prints them (finding 1).
2. Remove the four French film titles from the German films (finding 2).
3. Clear and credit the publisher fields (finding 3).
4. Mark Jurmann on the twelve songs, and the genre and instrumentation
   wording (finding 4).
5. Check *Sous le ciel de Venice* in Sieghardt, and the director of *Two
   Hearts in Wax Time*, when a copy is to hand.
