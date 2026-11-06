# The year of a Work

## The rule

A Work's year is the **earliest year in which the work itself is
documented**, by any of:

- a dated manuscript, read on the item or on a reproduction of it;
- a copyright registration, or an entry in a register such as Hofmeister;
- a publication;
- a recording session;
- the release of a film in which it was used.

Two further points follow from it:

- **A version dates its original.** A translated version cannot be earlier
  than the song it translates, so a dated version also dates the original.
  The German *Auf wiederseh’n, Herr Doktor* keeps 1929 because its Dutch
  version was printed in Vienna that year.
- **Later compilations do not move a year.** The Walter Jurmann catalogue
  and Sieghardt's work catalogue are good evidence for credits and for which
  film a song was written for, but they date films by production and are not
  themselves evidence of when a song existed.

A film's year is its first release. A song registered before the film does
not date the film.

## Why a rule was needed

The data followed two rules at once. The songs of *Everybody Sing* (1938)
were dated 1937, the year they were registered; the songs of *A Day at the
Races* (1937), registered in 1936, were dated 1937, the year of the film. The
same evidence gave different years depending on the film. Of the two rules,
the earliest documented year is the one that does not depend on which
evidence happens to be attached, and the one a reader can check against the
Sources on the card.

## What changed

Seventeen songs, checked one by one against their Sources.

**Earlier**

| Work | Was | Now | Earliest evidence |
| --- | --- | --- | --- |
| *Was macht jede Nacht so ein kleines Baby in der Bar?* | 1930 | 1927 | holograph manuscript, signed and dated Berlin 1927, read on a reproduction (`SRC0888`) |
| *Ich hab’ heut’ grad’ Geburtstag* | 1930 | 1929 | registered 10 October 1929 (`SRC0465`) |
| *Tränen in der Geige* | 1933 | 1932 | Hofmeister, November 1932, months before the film’s 1933 release |
| *The One I Love* | 1937 | 1936 | registered unpublished 17 February 1936 (`SRC0241`) |
| *Keep the Magic of Springtime* | 1937 | 1936 | registered as *Keep the Magic of Maytime*, 17 February 1936 |
| *At the Spats and Tennis Club* | 1937 | 1936 | registered 17 February 1936 |
| *Beyond My Fondest Dreams* | 1937 | 1936 | registered 6 July 1936 |
| *Blue Venetian Waters* | 1937 | 1936 | registered 7 November 1936 |
| *Tomorrow Is Another Day* | 1937 | 1936 | registered 16 November 1936 |
| *A Message from the Man in the Moon* | 1937 | 1936 | registered 16 December 1936 |

*The One I Love* was registered by the same authors and the same company
two years before *Everybody Sing*, on the day MGM registered *Tillie the
Tight Rope Walker* and *Who Knows*; the Jurmann catalogue knows only one
song of that title, written for *Everybody Sing*. The 1936 song and the 1938
film song are taken to be the same work, reused.

**Later**

| Work | Was | Now | Why |
| --- | --- | --- | --- |
| *Süße Mamsell, denkst du noch an das kleine Hotel* | 1929 | 1930 | every dated Source is of 1930 |
| *Wer weint heut’ aus Liebe Tränen?* | 1931 | 1932 | Hofmeister, February 1932; the film was released in 1932 |
| *Pourquoi donc verser des larmes* | 1931 | 1932 | its film, *Ehe mit beschränkter Haftung*, was released in 1932 |
| *Dit’s-moi, Madame* | 1931 | 1932 | French vocal edition of 1932 |
| *Ein Lied aus meiner Heimat* | 1931 | 1932 | Hofmeister, May 1932; *Melodie der Liebe* was reviewed on 27 April 1932 |
| *Once There Was a Baby* | 1932 | 1933 | the English version was registered in London in May 1933 |
| *My Heart Is a Gypsy* | 1938 | 1939 | registered 1939; *Balalaika* was released in 1939 |

The four 1931 songs had taken the year in which the Jurmann catalogue dates
their films, the year of production. *Ich frag’, Madame, wann kommen wir
zusamm’?*, from the same film, keeps 1931: it was recorded on 15 September
1931 (Kristall 3229).

## Checked and left

- *Sonny Boy* (1929) cites the 1928 score of the song Kaper transcribed for
  two pianos; the transcription is of 1929.
- *Quand une femm’ vous plaque* (1931) cites the 1930 registration of its
  German original.
- *The Sun Never Sets on Swing* (1937) cites a 1964 renewal, which gives the
  original copyright date, 5 August 1937.
- *Celui que j’aime* and *Dans la ferme d’amour* (1939) are the French
  editions of songs from *Everybody Sing*; the film's 1938 release dates the
  English songs, not the French texts.
- *O030 Piece for Voice and Orchestra* keeps 1928, as decided earlier: the
  1926 it is set against comes from an accession list, not from the
  manuscript.

`tests/test_work_years.py` holds the rule where it can be checked
mechanically: no Work is dated after its own copyright registration or after
a dated manuscript of it.
