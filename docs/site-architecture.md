# Public website architecture

## Objective

Replace the legacy hand-authored pages with a static, source-based research site
covering Bronisław Kaper's documented career through 1939. The same files must run
unchanged on GitHub Pages at `/kaper/`, on Netlify, and from a local static server.

## Public sections

| Route | Purpose | Canonical data |
| --- | --- | --- |
| `index.html` | Editorial introduction, scope, highlights and collection statistics | Works, Timeline Events, Media, Places |
| `works.html` | Searchable catalogue of films, songs and other works | Works and subtype tables |
| `life.html` | Source-based chronological timeline | Timeline Events |
| `map.html` | Geographic exploration with an accessible place list | Places and Timeline Events |
| `media.html` | Curated gallery, audio and external reference cards | Media |
| `record.html` | Linked detail view for works, events, places, media, people and sources | Public graph |

The existing `life.html` and `media.html` paths are retained to avoid breaking old
links. Detail records use query strings, which GitHub Pages serves without rewrite
rules, for example `record.html?type=work&id=W-F002`.

## Runtime model

- No Airtable API calls, authentication tokens or private backup files.
- No server-side code and no required JavaScript build step.
- Collection pages fetch versioned files from `data/public/v1/` using relative
  URLs and cache them for the lifetime of the page.
- A detail page fetches one generated, relation-aware bundle from
  `data/site/records/<type>/<id>.json`. The bundle contains the requested record
  and only the directly displayed public relations; it is rebuilt from the
  canonical tables and is never edited by hand.
- All linked records use stable public IDs, never Airtable record IDs.
- The map uses Leaflet only for the map interface and OpenStreetMap tiles; an
  equivalent searchable place list remains available if the map library or tiles
  are unavailable.

## Editorial and rights rules

- The visible scope is consistently labelled 1902–1939.
- Certainty and attribution qualifications are displayed rather than hidden.
- External media are linked, never automatically embedded.
- A fair-use media detail always displays its caption, source, credit line, rights
  status, rationale and limited-resolution local image where available.
- Source citations remain linked to the records they support.

## Deployment model

The repository root is the publish directory. Development happens on a feature
branch and is reviewed through a Netlify Deploy Preview. Production changes only
after an explicit merge to `main`, which preserves the current GitHub Pages URL.
The GitHub Pages URL is the default canonical origin unless a custom domain is
chosen before release.
