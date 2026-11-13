# Films audit, 13 November 2026

The 56 Film records were checked in three ways:

- each film's certainty against the certainty and Sources of Kaper's own
  credit;
- every film linked to filmportal.de, 27 in all, against the director,
  music credits and premiere dates its page gives;
- the American films against their AFI Catalog entries.

The years and directors were also compared with Wikidata. They agree for
24 films; the three differences are Wikidata's errors, or a 1962 remake of
the same title.

## Corrected

### Certainty

Six films were marked `confirmed` although Kaper's credit for each rests
only on later compilations, or on IMDb: Sieghardt's filmography, the
Walter Jurmann catalogue, or Görner's work list, which follows it. In line
with the archive's rule that Sieghardt is a secondary source and may err
where no document of the time supports him, the film, its Work and Kaper's
credit are now `probable`.

| Film | What the credit rests on |
|---|---|
| `F032` *Moscow Nights* (1935) | Sieghardt; the AFI entry (*I Stand Condemned*) names no composer |
| `F039` *Two Hearts in Wax Time* (1935) | Jurmann catalogue, Sieghardt, IMDb soundtrack; the copyright entry lists no credits |
| `F044` *Man of the People* (1937) | Jurmann catalogue and Sieghardt; AFI credits the score to Edward Ward alone and names no song by Kaper. AFI is removed from the credit's Sources |
| `F045` *Wings of the Morning* (1937) | IMDb alone; the credit itself was already `probable` |
| `F052` *Little Boy Blue* (1936) | Sieghardt and the Jurmann catalogue; the note already called it probable |
| `F054` *Un coup de rouge* (1937) | Sieghardt alone; the BnF holds the 1937 presentation booklet but records no music credit for Kaper |

### Credits

- **`F010` *Skandal in der Parkstraße*.** Kaper's credit cited filmportal,
  whose page names no composer. It now cites the *Illustrierter
  Film-Kurier* no. 1759, already among the film's Sources, which names
  “Dr. B. Kaper” and Jurmann for the music.
- **`F006` *Seitensprünge*.** Filmportal credits the music to Karl M. May,
  Kaper and Fritz German. Karl Michael May (`P113`) has a record here and
  now has his composer credit. Fritz German has no record, and the note
  names him.

## Checked and left as they are

- **`F016` *Voyage de noces*, 1933.** Filmportal's French premiere of 15
  December 1932 was a trade screening (*présentation corporative*). The
  public release was on 6 January 1933, as Unifrance also states; that
  was decided earlier and holds.
- **`F014` *Hochzeitsreise zu Dritt*.** Wikidata gives Joe May as director.
  Filmportal gives Erich Schmidt as director and Joe May for artistic
  supervision, as the record already does.
- **`F003` *Der Korvettenkapitän*.** Filmportal lists no music credit. The
  record rests on the *Kinematograph* advertisement and the Weimar Talkies
  Project, which name Kaper.
- **`F055`, `F056` and `F057`** have no film-level credit for Kaper, by
  design:
  - *Balalaika* is linked through its song;
  - *Coup de feu à l'aube* through its language-version relation;
  - *My Song for You* through the reuse of “Ninon”.
- **Remaining premieres.** All other filmportal premieres fall in the year
  the records give.

## Decided

**`F008` *Ehe mit beschränkter Haftung* is now dated 1931.** Filmportal gives
the German premiere as 31 December 1931, after censorship decisions of 11
and 30 December 1931. By the rule in `docs/work-years.md`, a film's year is
its first release. The song *Wer weint heut' aus Liebe Tränen?*, sung in the
film, follows to 1931. Its French version, *Pourquoi donc verser des
larmes*, keeps 1932 on the Eschig edition of that year.
