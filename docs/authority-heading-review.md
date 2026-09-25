# Authority-heading review — 25 September 2026

No `authorizedName` was changed. This review reports, for every person, what the
register linked in `authorityUrl` actually states, and where the archive's
heading departs from it. What was then acted on is recorded under *Applied*, at
the end; the rest stands as a worklist.

The starting point was an inconsistency in the data rather than in the rule.
`docs/authority-headings.md` puts the provenance of a heading in `authorityUrl`,
and that is filled for every person who has a register. The additional field
`authorizedNameSource`, which names the register the heading was transcribed
from, is filled for 95 of 177 people and for all 159 organizations. The question
was whether the 82 unlabelled headings could be labelled safely — which meant
first asking whether they are transcriptions at all.

## Method

Each person's `authorityUrl` lists its registers in precedence order; all 177
records do so correctly. The first machine-readable register was read for each:
LCNAF through `id.loc.gov/authorities/names/{id}.json`, taking the
`authoritativeLabel` of the node whose `@id` is the authority URI itself, and
GND through `lobid.org/gnd/{id}.json`, taking `preferredName`, as
`docs/person-life-dates-review.md` also did. Requests went out one at a time per
host, 0.6 seconds apart, with an identifying user agent. The date qualifier was
stripped from the register's heading before comparison, per the transcription
rule; nothing else was normalised, so a missing umlaut or an expanded initial
counts as a difference.

145 headings were read from LCNAF, 8 from GND. 15 people link only to registers
with no machine-readable form here (BnF, BN, NUKAT, VIAF, ISNI), and 9 have no
register at all.

## Summary

| | People |
| --- | --- |
| Heading confirmed against the register | 144 |
| — of these, carrying no `authorizedNameSource` | 76 |
| Heading differs from the register | 9 |
| Register not machine-readable — needs a human | 15 |
| Local heading, no register | 9 |

## What the differences show

Seven of the nine differences are one pattern: the archive follows the register
of the person's own language area, and LCNAF — which the rule puts first — holds
an anglicised, abbreviated or simply wrong form of the same name. LCNAF gives
`Guenther, Felix` where GND gives `Günther, Felix`; `Brull, Karl` for a Viennese
publisher; `Nazelles, R.` where BnF spells out René; `Mayer, Louis B. (Louis
Burt)` where GND stops at the initial. For Zygmunt Wiehler, LCNAF's heading is
`Wiehlera, Zygmunta` — the Polish genitive, read off a title page — and the
archive's `Wiehler, Zygmunt` is simply right.

The rule already contains this reasoning for one case: Róża Etkin, where BN
comes before GND so that a Polish musician is not catalogued as `Etkin, Rosa`.
The data applies the same reasoning more widely than the rule states. Either the
rule should say so — the register of the person's own language area comes
first, LCNAF otherwise — or these headings should change. That decision belongs
to the archive, and this review does not take it.

Two differences are not of that kind and need a separate decision; they are
marked below.

## Headings that differ from the register (9)

| Person | Archive heading | Register read | What it states | What it needs |
| --- | --- | --- | --- | --- |
| P093 René Nazelles | Nazelles, René | LCNAF | Nazelles, R. | Language-area pattern: BnF (the recorded source) spells the forename out. |
| P109 Henri Lemarchand | Lemarchand, **Henry** | LCNAF | Lemarchand, Henri | **Separate decision.** The record's own `displayName` is Henri, LCNAF is Henri, and `authorizedNameSource` names GND although no GND record is linked. |
| P114 Karl Brüll | Brüll, Karl | LCNAF | Brull, Karl | Language-area pattern; the recorded source is LexM, and LCNAF does hold a record, which the rule's fallback clause does not cover. |
| P116 Louis B. Mayer | Mayer, Louis B. | LCNAF | Mayer, Louis B. (Louis Burt) | GND states exactly the archive's form; only the precedence differs. |
| P121 Róża Etkin | Etkin, Róża | GND | Etkin, Rosa | Nothing: this is the exception the rule already names. |
| P130 Hermann Biek | Biek, Hermann | GND | Berlin, Ben | **Separate decision.** GND is the only register linked and it files him under his stage name. No `authorizedNameSource` is recorded. |
| P146 Felix Günther | Günther, Felix | LCNAF | Guenther, Felix | Language-area pattern; GND states the archive's form. |
| P169 Zygmunt Wiehler | Wiehler, Zygmunt | LCNAF | Wiehlera, Zygmunta | Nothing, except perhaps a note: LCNAF's heading is a genitive. GND and BN both give the archive's form. |
| P181 Pyotr Ilyich Tchaikovsky | Tchaikovsky, Pyotr Ilyich | LCNAF | Tchaikovsky, Peter Ilich | A transliteration choice, not a language-area case. No `authorizedNameSource` is recorded. |

### A. Ready to label — heading confirmed, no `authorizedNameSource` recorded (76)

| Person | Register | Heading as the register states it |
| --- | --- | --- |
| P002 Alfred Zeisler | LCNAF | Zeisler, Alfred |
| P003 Andrzej Włast | LCNAF | Włast, Andrzej, 1895-1942 or 1943 |
| P007 Anthony Asquith | LCNAF | Asquith, Anthony, 1902-1968 |
| P012 Desmond Carter | LCNAF | Carter, Desmond |
| P013 Edwin L. Marin | LCNAF | Marin, Edwin L., 1901-1951 |
| P017 Ernst Marischka | LCNAF | Marischka, Ernst |
| P018 Frank Lloyd | LCNAF | Lloyd, Frank, 1887-1960 |
| P019 Franz Wenzler | LCNAF | Wenzler, Franz |
| P020 Fritz Rotter | LCNAF | Rotter, Fritz |
| P022 Georg Jacoby | LCNAF | Jacoby, Georg |
| P023 George B. Seitz | LCNAF | Seitz, George B., 1888-1944 |
| P027 Hans Steinhoff | LCNAF | Steinhoff, Hans, 1882-1945 |
| P028 Harold Adamson | LCNAF | Adamson, Harold |
| P029 Harold D. Schuster | LCNAF | Schuster, Harold D., 1902-1986 |
| P030 Heinz Hilpert | LCNAF | Hilpert, Heinz, 1890-1967 |
| P031 Henri Varna | LCNAF | Varna, Henri |
| P034 Henry Koster | LCNAF | Koster, Henry, 1905-1988 |
| P037 J. Walter Ruben | LCNAF | Ruben, J. Walter |
| P039 Jean Choux | LCNAF | Choux, Jean |
| P044 Joe May | LCNAF | May, Joe, 1880-1954 |
| P045 Joseph H. Lewis | LCNAF | Lewis, Joseph H., 1907-2000 |
| P046 Joseph Santley | LCNAF | Santley, Joseph, 1889-1971 |
| P047 Carl Meinhard | GND | Meinhard, Carl |
| P048 Kurt Gerron | LCNAF | Gerron, Kurt, 1897-1944 |
| P049 Louis Poterat | LCNAF | Poterat, Louis, 1901-1982 |
| P052 Marc-Cab | LCNAF | Marc-Cab |
| P054 Max Kolpe | LCNAF | Kolpe, Max |
| P055 Max Obal | LCNAF | Obal, Max, 1881-1949 |
| P058 Ned Washington | LCNAF | Washington, Ned, 1901-1976 |
| P062 Oscar Micheaux | LCNAF | Micheaux, Oscar, 1884-1951 |
| P063 Pierre Billon | LCNAF | Billon, Pierre, 1901-1981 |
| P065 René Pujol | LCNAF | Pujol, René, 1888-1942 |
| P066 Richard Oswald | LCNAF | Oswald, Richard, 1880-1963 |
| P067 Richard Thorpe | LCNAF | Thorpe, Richard, 1896-1991 |
| P068 Robert Péguy | LCNAF | Péguy, Robert, 1883-1968 |
| P070 Robert Z. Leonard | LCNAF | Leonard, Robert Z., 1889-1968 |
| P071 Roger Edens | LCNAF | Edens, Roger, 1905-1970 |
| P072 Roger Féral | LCNAF | Féral, Roger |
| P074 Sam Wood | LCNAF | Wood, Sam, 1883-1949 |
| P075 Tim Whelan | LCNAF | Whelan, Tim, 1893-1957 |
| P077 Walter Jurmann | LCNAF | Jurmann, Walter, 1903-1971 |
| P086 Austin Egen | LCNAF | Egen, Austin |
| P092 Gaston Roudès | LCNAF | Roudès, Gaston, 1878-1958 |
| P095 Reinhold Schünzel | LCNAF | Schünzel, Reinhold, 1888-1954 |
| P097 Frank Eyton | LCNAF | Eyton, Frank |
| P105 Hermann Scheibenhofer | GND | Scheibenhofer, Hermann |
| P125 Ernst Lubitsch | LCNAF | Lubitsch, Ernst, 1892-1947 |
| P126 Robert Gilbert | LCNAF | Gilbert, Robert, 1899-1978 |
| P127 Friedrich Jung | GND | Jung, Friedrich |
| P131 Józef Śmidowicz | LCNAF | Śmidowicz, Józef, 1888-1962 |
| P132 Henri Garat | LCNAF | Garat, Henri, 1902-1959 |
| P133 Eddy Duchin | LCNAF | Duchin, Eddy, 1909-1951 |
| P134 Ivie Anderson | LCNAF | Anderson, Ivie |
| P135 Franz Waxman | LCNAF | Waxman, Franz, 1906-1967 |
| P136 Herbert Stothart | LCNAF | Stothart, Herbert, 1885-1949 |
| P137 Deanna Durbin | LCNAF | Durbin, Deanna |
| P138 Judy Garland | LCNAF | Garland, Judy |
| P140 William Axt | LCNAF | Axt, William, 1882-1959 |
| P141 Edward Ward | LCNAF | Ward, Edward, 1896-1971 |
| P142 Willy Schmidt-Gentner | LCNAF | Schmidt-Gentner, Willy, 1894-1964 |
| P143 Hans J. Salter | LCNAF | Salter, Hans J. |
| P144 Paul Dessau | LCNAF | Dessau, Paul, 1894-1979 |
| P145 Hans-Otto Borgmann | LCNAF | Borgmann, Hans-Otto |
| P147 Marc Lavry | LCNAF | Lavry, Marc, 1903-1967 |
| P149 Franz Grothe | LCNAF | Grothe, Franz, 1908-1982 |
| P150 Nicholas Brodszky | LCNAF | Brodszky, Nicholas |
| P151 Paul Mann | LCNAF | Mann, Paul, 1910-1983 |
| P153 Hans Albers | LCNAF | Albers, Hans |
| P154 Alfred Piccaver | LCNAF | Piccaver, Alfred, 1884-1958 |
| P157 Ub Iwerks | LCNAF | Iwerks, Ub, 1901-1971 |
| P158 Carl W. Stalling | LCNAF | Stalling, Carl W. |
| P159 Julian Tuwim | LCNAF | Tuwim, Julian, 1894-1953 |
| P161 Carl Laemmle | LCNAF | Laemmle, Carl, 1867-1939 |
| P162 Paul Kohner | LCNAF | Kohner, Paul |
| P182 Ray Henderson | LCNAF | Henderson, Ray, 1896-1970 |
| P195 Johnny Green | LCNAF | Green, Johnny, 1908-1989 |

### B. Already labelled, heading confirmed (68)

Nothing to do. In ten of them the recorded source names a different register from the one read here, and the two agree on the form: P021 (BnF recorded, LCNAF read), P038 (GND recorded, LCNAF read), P057 (GND recorded, LCNAF read), P082 (GND recorded, LCNAF read), P088 (GND recorded, LCNAF read), P110 (BnF recorded, LCNAF read), P123 (GND recorded, LCNAF read), P124 (BnF recorded, LCNAF read), P175 (BN recorded, GND read), P198 (BnF recorded, LCNAF read).

### C. Not machine-readable — a human has to read the register (15)

| Person | Archive heading | Recorded source | Registers linked |
| --- | --- | --- | --- |
| P004 André Auguste Saudemont | Saudemont, André | local heading | VIAF |
| P014 Egon Schubert | Schubert, Egon | local heading | VIAF |
| P015 Erich Schmidt | Schmidt, Erich | GND | VIAF, Wikidata |
| P016 Erich von Neusser | Neusser, Erich von | GND | VIAF, Wikidata |
| P024 Germain Fried | Fried, Germain | LCNAF | VIAF, Wikidata |
| P043 Jean-René Legrand | Legrand, Jean-René | LCNAF | VIAF, Wikidata |
| P060 Ninon Steinhoff | Steinhof, Ninon | BnF | BnF, VIAF, ISNI |
| P069 Robert Wohlmuth | Wohlmuth, Robert | BnF | VIAF, Wikidata |
| P087 Norman Hackforth | Hackforth, Norman P. | LCNAF | VIAF, Wikidata |
| P096 Ferry van Delden | Delden, Ferry van | Dutch National Thesaurus (NTA), via VIAF cluster | VIAF, ISNI, Wikidata |
| P106 Charlie Davson | Davson, Charlie | — | BnF, ISNI |
| P108 Didier Mauprey | Mauprey, Didier | — | BnF |
| P113 Karl Michael May | May, Karl Michael | BnF | BnF, VIAF |
| P155 Georges Rey | Rey, Georges | — | BnF |
| P156 Marcella Halicz | Halicz, Marcella | — | BN, NUKAT, VIAF, ISNI |

### D. Local headings — no register holds the person (9)

P061 Oliver Perry, P079 André Roubier, P090 Giuliano Pomeranz, P098 H. Hailey-Simpson, P115 A. Oliver, P129 Eleonora Kaper, P160 Eliza Rozenblum, P200 Ralph Stanley, P201 Ralph Jack. All nine are marked `local heading`, which is what the rule asks for.

## If the labels are to be filled

Group A can be labelled from this reading: for each of the 76, the register read
states the archive's heading exactly once the date qualifier is removed. Group C
needs the register opened by hand — five people whose first register is BnF,
one catalogued by BN and NUKAT, and nine known only to VIAF or Wikidata, where
the rule's last clause asks for the actual register to be named. Groups B and D need nothing.

Whether to fill the field at all is a separate question from this review: the
rule puts provenance in `authorityUrl`, and `authorizedNameSource` duplicates it
in a shorter form. It is filled for every organization, which is the argument
for filling it for every person too.

## Applied, 25 September 2026

**Group A was labelled.** The 76 people whose heading the register states
exactly now carry `authorizedNameSource`: LCNAF for 73, GND for 3, in each case
the first register their own record links. The field is rendered on the person
card as “Heading source”, so the cards no longer divide into those that say
where a heading comes from and those that do not.

**Eleven records named a register they did not link.** The card claimed a
heading source a reader could not open. Eight were resolved by asking the
register itself, and an identifier was added only where the register states the
archive's heading and the same life dates, or names the record's own VIAF and
LCNAF URIs as the same entity:

| Person | Added | The register states |
| --- | --- | --- |
| P015 Erich Schmidt | GND 1274108136 | Schmidt, Erich; 13 August 1892 – 6 September 1971 |
| P016 Erich von Neusser | GND 1062461193 | Neusser, Erich von; 23 October 1902 – 28 August 1957 |
| P024 Germain Fried | LCNAF n2009070290 | Fried, Germain |
| P043 Jean-René Legrand | LCNAF no2011174144 | Legrand, Jean-René |
| P057 Max Reichmann | GND 116402733 | Reichmann, Max; 1884–1958 |
| P087 Norman Hackforth | LCNAF n2008017509 | Hackforth, Norman P. |
| P088 Leopold Mittmann | GND 134838068 | Mittman, Leopold; 16 September 1904 – June 1976, its sameAs naming this record's own LCNAF and VIAF URIs |
| P109 Henri Lemarchand | GND 1258427923 | Lemarchand, **Henry**; 1911–1991, its sameAs naming this record's own LCNAF, VIAF and Wikidata URIs |

P109 settles half of the question left open above. The heading's `Henry` is
GND's form, and GND is where the record's life dates come from; only the
identifier was missing. Whether a French lyricist should be filed under GND's
`Henry` or LCNAF's `Henri` is still a decision, but it is now a decision between
two registers rather than a suspected slip.

Three remain open: **P069 Robert Wohlmuth**, whose record names BnF, and
**ORG030 Éditions Coda** and **ORG032 Éditions musicales universelles**, which
name BnF and link nothing at all. Wikidata gives a BnF identifier for Wohlmuth,
`17166302h`, but catalogue.bnf.fr did not answer while this was written and an
identifier the register has not confirmed was not added. `tests/test_authority_headings.py`
holds the three as a named exception and fails on any new one.

**Still open, and untouched**: the nine differing headings, the precedence
question behind seven of them, the fifteen people whose register is not
machine-readable here, and whether P096 Ferry van Delden and P114 Karl Brüll —
whose headings come from the Dutch national thesaurus and from LexM — should
carry identifiers for those registers, as the rule's last clause asks.
