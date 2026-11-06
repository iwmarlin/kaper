# Evidence context on contributions

`evidenceContext` is internal metadata. It is filled on 683 of 1327
Contributions and holds 26 distinct snake_case values, and unlike every
vocabulary a reader sees — `SOURCE_TYPES`, the role badges, the certainty
labels — it has no display form. This page records what it actually contains,
because its name promises one thing and the data holds two.

## It answers two different questions

Of the 683 values, 629 name **the kind of document that attested the credit**:

| Value | n | Roles |
| --- | --- | --- |
| `sheet_music` | 230 | publisher, arranger, composer and 2 more |
| `film_credits` | 181 | composer, production_company and 10 more |
| `recording_label` | 115 | performer, record_label, conductor and 2 more |
| `online_catalogue` | 31 | record_label, performer, conductor and 2 more |
| `discography` | 29 | record_label, performer, conductor |
| `newspaper_or_periodical` | 10 | performer, composer, lyricist |
| `archival_catalogue` | 8 | holding_institution |
| `secondary_literature` | 8 | composer, film_director and 2 more |
| `copyright_catalogue` | 5 | copyright_claimant, composer, lyricist |
| eight further document values | 12 | various |

Another 46 name **what the person contributed**, which is not evidence at all:

| Value | n | Roles |
| --- | --- | --- |
| `original_composition` | 23 | composer |
| `film_song` | 12 | composer, performer, conductor |
| `film_songs` | 4 | composer |
| `stock_music` | 3 | composer |
| `background_music` | 2 | composer |
| `background_music_and_song` | 1 | composer |
| `additional_music` | 1 | composer |

Nine values are compounds joining two statements with `_and_`, in four
spellings, and they do not all join the same kind of thing. Counting them as
one group hides that:

| Compound | n | What it joins |
| --- | --- | --- |
| `film_credits_and_song_catalogue` | 6 | two documents — film credits and a song catalogue |
| `background_music_and_song` | 1 | two contributions — a score and a song |
| `film_song_and_song_catalogue` | 1 | one of each |
| `film_credits_and_background_music` | 1 | one of each |

So the 683 values divide as 635 about documents (629 simple and 6 compound),
46 about the contribution (including `background_music_and_song`), and 2 that
state one of each at once. The six document compounds are not misplaced, only
packed: they belong on the evidential side and need splitting into a list, not
moving.

The distinction is visible in the records themselves. A document value spreads
across roles — `film_credits` appears on twelve of them — because any credit
can be attested by a film's credits. A contribution value is almost always
`composer`, and its `scopeNote` describes the music rather than the source:
`stock_music` on *The Spy Ring* reads “Pre-existing or reused music; not a
principal film-score credit,” and `background_music` on *Little Boy Blue* reads
“Background cues for the animated short.”

## What is not drift

`film_song` and `film_songs` look like a singular slipped against a plural.
They are not, and the data settles it without an editorial ruling: **the number
says how many songs the credit covers, and it is right on all eighteen
records.**

Twelve of the eighteen sit on a film, as composer credits shared by Kaper and
Jurmann, and the number matches the songs the archive holds for that film every
time:

| Film | value | songs |
| --- | --- | --- |
| *Mutiny on the Bounty* | `film_song` | 1 |
| *A Night at the Opera* | `film_song` | 1 |
| *Kind Lady* | `film_song` | 1 |
| *Skandal in der Parkstraße* | `film_songs` | 2 |
| *Last of the Pagans* | `film_songs` | 2 |
| *Le chant du destin* | `film_songs` | 4 |

The remaining six carry `film_song` on a song rather than a film — Allan Jones
and Richard Tauber as performers, Paul Dessau conducting — where the singular
is right by definition, because the credit is for the one song the record is.

*Mutiny on the Bounty* is the case worth keeping, because it looks like a
counter-example and is not. Two songs name that film as their source, “Love
Song of Tahiti” and “Chanson d’amour de Tahiti”, but the second is tied to the
first by `language_version_of` while only the first is `associated_with_film`.
The singular counts the work, not its language versions, which is the
distinction the relations already draw.

So the two spellings carry a fact and must not be merged. What they do not
carry is a controlled form: a credit covering three songs would have nowhere to
say so, and the count lives in a suffix rather than in a field.

## The uneven coverage

The 644 records with no value are not spread evenly. They follow the role:

| Role | n | missing | % |
| --- | --- | --- | --- |
| lyricist | 228 | 208 | 91% |
| film_director | 62 | 58 | 94% |
| composer | 527 | 365 | 69% |
| arranger | 23 | 5 | 22% |
| publisher | 204 | 8 | 4% |
| 12 further roles | 283 | 0 | 0% |

An archive about Kaper might reasonably leave his own credits without a
context, but that is not what happened. Of the 365 composer credits with no
value, 160 belong to other composers, and Kaper's own 273 composer credits are
themselves split, 68 with a context and 205 without. The gap follows the batch
a credit arrived in.

## It does not reach a reader, and did not

`evidenceContext` stood third in one branch of the credit note, behind
`scopeNote` and `publicNote`. That branch ran only when a work's credits were
not the concise ones, and every work is a song, a film or an other work, so it
never ran: no page has ever printed one of these tokens. Had a fourth work type
appeared, `workType` being neither controlled nor validated, the branch would
have begun printing `film_credits_and_song_catalogue` to readers verbatim. The
fallback is gone, and `tests/test_evidence_context.py` holds the line.

Publishing the field would first require a display vocabulary, and that cannot
be written while one column answers two questions.

## One value carries rendering logic

On an other work, `evidenceContext == "original_composition"` is what separates
the “Music and arrangement” section from the remaining credits. 23 credits
across 18 works depend on it, and the comparison is against a free-text field
with no controlled vocabulary, so renaming the value would silently drop a
section from eighteen pages. `tests/test_evidence_context.py` pins the value,
checks that it appears only on other works, where the renderer reads it, and
checks that every flagged work still shows the section.

## The film record states it too, at its own level

`films.creditType` states the same distinction at the level that owns it — the
film's credit rather than one contribution — with a coherent vocabulary:
`composer` (26), `songwriter` (19), `music_direction` (3), `stock_music` (3),
`background_music` (2), `music_score` (1), `uncertain` (1), on 55 of 56 films.
`films.attributionNote` then gives it in prose on 31 of them: *Mutiny on the
Bounty* reads “Song ‘Love Song of Tahiti’ … uncredited on screen”, and *A Night
at the Opera* “score by Herbert Stothart; songs by Kaper”.

So for a film, `evidenceContext` and `films.creditType` can state the same
thing at two levels, and where they do, copies drift. On four films the two say
different things — but not for the same reason, and only one is likely to be an
error:

**W-F052 Little Boy Blue.** Corrected. Both credits read `background_music`,
both `scopeNote`s read “Background cues for the animated short,” and the
`attributionNote` quotes the Jurmann catalogue's “Hintergrundmusik für Little
Boy Blue”, while `creditType` alone said `composer`. It now reads
`background_music`, a value the field already carries on two other films.

**W-F013 Die Zwei vom Südexpreß.** Not a drift. Its `attributionNote` says so
in as many words — “Both attributions are retained as source-specific” —
because Filmportal credits Kaper and Friedrich Jung under *Musik* while the
Jurmann catalogue gives the background music and one song to Kaper and Jurmann.
`creditType` follows the first source and the credit follows the second, on
purpose.

**W-F010 Skandal in der Parkstraße and W-F027 Le chant du destin.** Corrected.
The disagreement here was inside the film rather than between the levels:
Kaper's credit read `film_credits`, naming the document, and Jurmann's
`film_songs`, naming the contribution, for one joint credit. On W-F010 both
`scopeNote`s state the identical fact and name the same two songs, and S066 and
S067 each carry Kaper and Jurmann as composers. On W-F027 the film's four
songs, W-S088 to W-S091, do the same: the printed edition credits Pierre
Candel, the pseudonym standing for Jurmann alone, and the official Jurmann
works catalogue records the songs as written in collaboration with Kaper. Both
credits now read `film_songs`, which is how the archive states two
song-writers elsewhere — on *Mutiny on the Bounty* and *A Night at the Opera*
both read `film_song` and the separately credited score composer, Herbert
Stothart, is the one reading `film_credits`.

`creditType` was left at `composer` on both. Nothing in either film's sources
names a different score composer, as *Mutiny on the Bounty* names Stothart, so
the narrower `songwriter` would assert more than the evidence carries; and
W-F027 is the French-language version of W-F026, which would then have to move
with it.

Neither field is validated, so nothing caught any of this. Note also that
`creditType` and `attributionNote` did not reach a reader either, which is a
separate finding recorded in `docs/public-data-audit.md`; the card now states
them.

## Decision: the credit-level value stands

The contribution values stay where they are. `films.creditType` states the
same thing for many of these films, but it is **one value per film**, and a
contribution is per person: on *Little Boy Blue* Kaper and Jurmann wrote the
background cues while Carl W. Stalling wrote additional music, and the
film-level field cannot say that. Retiring the credit-level value would remove
a distinction the schema has nowhere else to put. The four overrides that set
it deliberately — “songwriter for ‘Love Song of Tahiti,’ not composer of the
complete film score” and its three siblings — were right about the level.

What remains open is narrower and is hygiene rather than modelling: the four
`_and_` spellings should become a list, and whether `film_song` against
`film_songs` carries a real distinction in number is still unanswered. Neither
blocks anything.

The analysis that led here is kept below, because it is the reason the answer
is not the obvious one.

## The case that was considered and rejected

For films the separation looked like a deletion: `films.creditType` already holds the
contribution with a vocabulary, at the right level, for 55 of 56 films.

The 46 contribution values do not all have that home, and the difference
matters, because `creditType` is a field of `films` alone:

| Where the value sits | n | What can absorb it |
| --- | --- | --- |
| On a film | 17 | `films.creditType` — these can be retired |
| On an other work (all `original_composition`) | 23 | nothing: other works have no `creditType`, and the renderer reads this value to split “Music and arrangement” |
| On a song (all `film_song`) | 6 | nothing, but these are performer and conductor credits whose `scopeNote` already says it in prose |

So retirement covers 17 values, not 46, and it needs the disagreements below
reconciled first, one editorial decision each. The 23 on other works are the
opposite case: if anything they should be promoted to a controlled field of
their own, parallel to `films.creditType`, rather than dropped. Only once the
field means one thing does “required for this role” have a definite meaning,
and only then can it be controlled or published.

### Why the retirement was not carried out

Of the 27 film credits holding a value on the contribution axis, 13 are cases
where `films.creditType` already states the same thing, so the value looked
safe to drop: W-F032 and W-F049 (`stock_music`), W-F034, W-F035, W-F036 and
W-F037 (`film_song`, `film_songs`, against `songwriter`), and W-F052
(`background_music`). Ten of those 13 carry no `scopeNote`, so the field is the
only per-credit record of the contribution.

Four of them then turned out to carry an override whose written reason is
exactly that intent: “Model Kaper's Mutiny on the Bounty contribution at its
documented scope: songwriter for ‘Love Song of Tahiti,’ not composer of the
complete film score,” and the same for *Last of the Pagans*, *A Night at the
Opera* and *Kind Lady*. Each of those four also removes the `scopeNote`
deliberately, so the structured fields were meant to carry the statement in its
place. That is not import residue, and dropping the value would undo a reasoned
editorial decision.

Those same four overrides also set `role` to `songwriter`, which the data does
not have and which is not in the role vocabulary at all — so they come from a
model that was afterwards partly abandoned, and they cannot simply be read as
current intent either. The question that has to be answered first is therefore
narrow and concrete: was the credit-level modelling superseded when
`films.creditType` came to state the same thing, or is it meant to stand beside
it? The remaining 14 of the 27 need no such ruling and are described above —
six are two documents packed into one string, two mix an axis each, one is
Stalling's `additional_music`, which is per person where `creditType` is per
film, and five are W-F010, W-F013 and W-F027.
