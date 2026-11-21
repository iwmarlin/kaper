# Site layer audit

21 November 2026. A pass over the generated site as a reader meets it: the
static HTML, the pages as a browser renders them at desktop and phone widths,
and an automated accessibility check.

## What was checked

- **Internal links.** Every `href` and `src` in all 2,212 HTML files was
  resolved against the page's `<base href>` and checked on disk, as was every
  candidate in every `srcset` (2,572 image URLs) and every same-page or
  cross-page `#fragment`. No broken target, no missing image file, no dead
  anchor.
- **Sitemap.** All 2,196 `<loc>` URLs exist. The 14 record pages left out of it
  are the redirects that `LEGACY_WITHDRAWN_REDIRECTS` writes for withdrawn or
  merged records (TE0045, ORG007, P157, P158, M197 and the rest), each with
  `noindex` and a refresh to the record that replaced it. Correct as is.
- **Records against pages.** Every record in `data/public/v1` has a page, and
  every page is either a live record or a redirect. No orphan pages.
- **Page furniture.** Every page has a `lang`, a non-empty and unique
  `<title>`, exactly one `<h1>` and no duplicate `id`s. Every `<img>` carries an
  `alt`. Only `404.html` has no meta description and no canonical link, and
  `record.html` (the client-side fallback) has no canonical link. Both are
  right for those pages.
- **In the browser.** Headless Chromium opened every live record page (2,188)
  at 390 px wide, and the ten top-level pages plus every fifteenth record of
  each kind at 1366 px: 2,357 loads in all. Each was checked for console
  errors, uncaught exceptions, failed or 4xx requests, images that did not
  decode, horizontal overflow and visible empty sections or headings. None of
  these turned up. The only failed requests reported were the five audio files
  of M010–M014 (`net::ERR_ABORTED`). That is Chromium cancelling a buffering
  request, not a fault: the players reach `readyState` 4 with the full
  durations (224, 73 and 257 seconds for the three Sonatina movements).
- **Accessibility.** axe-core 4.10 on the ten top-level pages and one record
  of each kind, at both widths. The site's Content Security Policy
  (`script-src 'self'`) blocks the injected checker, as it should, so CSP was
  bypassed in the test browser only.

## What was changed

- **Nested complementary landmark.** The side column of every record page was
  an `<aside>` inside `<main>`, which axe reports as
  `landmark-complementary-is-top-level` (moderate). It is now a
  `<div class="record-layout__aside">`. The one style rule that hid it on
  single-column records follows the new class. The layout is unchanged:
  beside the record at desktop width, under it on a phone. After the rebuild
  axe reports no violations on any page checked.
