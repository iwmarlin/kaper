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

Another 45 name **what the person contributed**, which is not evidence at all:

| Value | n | Roles |
| --- | --- | --- |
| `original_composition` | 23 | composer |
| `film_song` | 12 | composer, performer, conductor |
| `film_songs` | 4 | composer |
| `stock_music` | 3 | composer |
| `background_music` | 2 | composer |
| `additional_music` | 1 | composer |

The remaining 9 are compounds that join two statements with `_and_`, in four
spellings: `film_credits_and_song_catalogue` (6),
`film_song_and_song_catalogue`, `film_credits_and_background_music` and
`background_music_and_song`. Some join two documents, others two kinds of
contribution.

The distinction is visible in the records themselves. A document value spreads
across roles — `film_credits` appears on twelve of them — because any credit
can be attested by a film's credits. A contribution value is almost always
`composer`, and its `scopeNote` describes the music rather than the source:
`stock_music` on *The Spy Ring* reads “Pre-existing or reused music; not a
principal film-score credit,” and `background_music` on *Little Boy Blue* reads
“Background cues for the animated short.”

## What is not drift

`film_song` and `film_songs` look like a singular slipped against a plural, and
may not be: Kaper wrote one song for *Mutiny on the Bounty* and more than one
for *Last of the Pagans*. Whether the number is meaningful is an editorial
question, and the two spellings must not be merged before it is answered.

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

## The contribution half is already held elsewhere, and better

`films.creditType` states the same distinction at the level that owns it — the
film's credit rather than one contribution — with a coherent vocabulary:
`composer` (26), `songwriter` (19), `music_direction` (3), `stock_music` (3),
`background_music` (2), `music_score` (1), `uncertain` (1), on 55 of 56 films.
`films.attributionNote` then gives it in prose on 31 of them: *Mutiny on the
Bounty* reads “Song ‘Love Song of Tahiti’ … uncredited on screen”, and *A Night
at the Opera* “score by Herbert Stothart; songs by Kaper”.

So the contribution half of `evidenceContext` is a second copy of a statement
the film record already makes. Copies drift, and these have: on four films the
two disagree, the film saying `composer` while the credit says the contribution
was songs or background cues only.

| Film | `films.creditType` | `evidenceContext` |
| --- | --- | --- |
| W-F010 Skandal in der Parkstraße | `composer` | `film_songs` |
| W-F013 Die Zwei vom Südexpreß | `composer` | `background_music_and_song` |
| W-F027 Le chant du destin | `composer` | `film_songs` |
| W-F052 Little Boy Blue | `composer` | `background_music` (two credits) |

Neither field is validated, so nothing catches the disagreement. Note also
that `creditType` and `attributionNote` do not reach a reader either: both are
carried into the record payload and never rendered, so the qualification that
separates a song credit from a score credit is recorded three times over and
published none of them. That is a separate finding, in
`docs/public-data-audit.md`.

## Open decision

Whether the field is required cannot be settled while it means two things. The
question to answer first is whether to separate them, and the evidence above
suggests the separation is really a deletion: the evidential half stays in
`evidenceContext`, and the contribution half belongs to `films.creditType`,
which already holds it with a vocabulary, at the right level, for every film.
Retiring those 54 values would mean reconciling the four disagreements first,
one editorial decision each. Only then does “required for this role” have a
definite meaning, and only then can the field be controlled or published.
