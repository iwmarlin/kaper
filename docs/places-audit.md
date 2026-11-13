# Places audit, 13 November 2026

The 45 Place records were read against their notes, their sources and the
Timeline Events they serve. Every documented address was then geocoded
through the OpenStreetMap Nominatim API and the distance to the record's
marker measured.

## Corrected

### Coordinates

Ten markers stood 120–790 m from the address their own note gives. Each was
moved to the OpenStreetMap address point:

| Place | Address | Was off by |
|---|---|---:|
| `PL006` MGM Studios | 10202 West Washington Boulevard, Culver City | 789 m |
| `PL009` Staszic Gymnasium | Noakowskiego 6, Warsaw | 463 m |
| `PL037` Sievering studio | Sieveringer Straße 135, Vienna | 491 m |
| `PL015` Skrynnikow school | Żurawia 49, Warsaw | c. 320 m |
| `PL011` St. Alexander's Church | Plac Trzech Krzyży, Warsaw | 202 m |
| `PL007` | Wilcza 29, Warsaw | 194 m |
| `PL040` Polish Consulate General | 19 rue Alphonse-de-Neuville, Paris | 171 m |
| `PL010` / `PL017` Philharmonic | Jasna 5, Warsaw | 170 m |
| `PL035` Château Frontenac | 54 rue Pierre-Charron, Paris | 127 m |

The MGM marker had stood in central Culver City rather than on the studio
lot.

### Notes and names

- **`PL046` Perskie Oko.** The theatre had two addresses in 1926: Nowy Świat
  63 until 11 September, then Marszałkowska 125. The 1926 editions do not
  say in which month the songs were introduced. The note now says so, and
  the precision is `site_approximate`.
- **`PL031` Babelsberg.** The authorized name carried the present name,
  Studio Babelsberg, which dates from after 1990. It now gives Ufa's
  studios at Neubabelsberg, the name they had in 1931–1933, with the
  present name in brackets.

### Event links

- `TE0060`, the Morskie Oko premiere, now also links `PL001` Warsaw, as
  every other Warsaw event does.
- `TE0058`, the Bach-Saal recital, had no place display. It now reads
  Berlin.

## Left as they are

- **`PL014` Sienna 44.** OpenStreetMap has no house number 44, and the note
  already says that continuity between the 1902 property and the modern
  numbering is unverified.
- **`PL043` Calexico–Mexicali crossing.** The marker is placed at the foot of
  Heffernan Avenue, where the 1933 inspection station stood. The
  OpenStreetMap point is the middle of the avenue, so the difference of
  145 m is expected.
- **`PL032` Joinville.** Paramount's multiple-language versions were made at
  the studios in Saint-Maurice, which were commonly called Joinville; the
  Pathé studios stood in Joinville-le-Pont itself. The record is
  `context_only` with a city-level marker, so the question does not move
  the map. If it is ever made more precise, the studio should first be
  identified from the 1929 *Pour Vous* article it cites.
- **Region names** (`Masovian Voivodeship`, `Normandy`) are present-day
  administrative names. They serve to locate a place, not to describe it
  historically. Names of the time are carried by the authorized names and
  the notes.

## Checked and found sound

- **Twelve further markers** lie within 85 m of their address point: the
  George V, Ritz, Casino de Paris, Hotel Edison, Château des Fleurs,
  Pommersche Straße 3, Universum, Bach-Saal, Kabarett der Komiker, the
  Okólnik conservatory, Studio Babelsberg and Nowy Świat 63.
- **Precision values** match the notes. Every `site_approximate` record says
  what the marker does and does not claim.
- **City and district markers** fall in the right city or district.
- **Every Place** is linked to at least one Timeline Event, and the links run
  both ways. The periods derived from the events match.
- **`context_only` places** (Vienna, Babelsberg, Joinville, Sievering) are
  context for the multiple-language and star-singer events and make no
  claim about Kaper's presence.
