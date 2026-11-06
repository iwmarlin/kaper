# External video-source review — 26 October 2026

The reviewed family contains 21 Sources and their 20 existing Media. No new
People, Songs, Works, Organizations or Media were created. All twelve YouTube
items contain moving images and remain video, including the modern stage
performance and edited presentations. Publication metadata and sampled video
storyboard frames were examined; no claim of frame-by-frame examination of
every feature film is made.

| Sources | Material and date meaning |
| --- | --- |
| SRC0010 | PBS/WNET contextual documentary video; page publication 1 December 2008, not a Kaper employment or music credit. The page supplies an MP4 embed. |
| SRC0314 | Modern staged performance; YouTube publication 29 March 2019, production dated 2014 by the uploader. Not footage from Kind Lady. |
| SRC0315–SRC0316 | Historical film excerpts; dates now identify the verified YouTube publications, not the historical films. |
| SRC0317 | Feature-length French Les nuits moscovites (1934), not English Moscow Nights (1935). Opening/closing titles and English subtitles are present; an uncut edition is not certified. |
| SRC0318, SRC0320–SRC0321 | Musical-number film excerpts; dates identify the YouTube publications, not commercial discs. |
| SRC0319 | Edited film presentation; uploader explicitly describes a restored and sweetened soundtrack. Not represented as an untouched soundtrack master. |
| SRC0322–SRC0325 | Filmportal opening excerpts. Retain explicitly stated digitization years 2021, 2023, 2024 and 2022; distinguish posting dates and listed runtimes. The Murnau-Stiftung is named for its actual digitization-source role where applicable, separately from the Filmportal/DFF access platform. |
| SRC0327 | TCM film page containing a four-minute “Someone To Care For Me” clip, not a standalone audio link. Regional redirects limit playback; no additional Media created. |
| SRC0555 | Twenty-two-second My Footage studio montage; YouTube publication 3 June 2010. Licensing offer is not permission to reuse. Context, not an individual Kaper production credit. |
| SRC0681–SRC0682 | Institutional access copies: production year and technical/filmographic metadata reread in the actual Bundesarchiv interface. Madame lists production 1932 and censorship 9 January 1933; Südexpress lists production 1932. These are not digital publication dates. |
| SRC0683 | Structural and date-role review only. Fresh access to both the item URL and the film-level URL remained on the loading screen. Prior catalogue data and the existing access date 13 August 2026 are retained, not falsely reverified. |
| SRC0733 | Edited film-scene presentation of Piccaver; YouTube publication 29 October 2017, not a separately identified disc. |
| SRC0791 | Ein toller Einfall excerpt containing the answering song form. Remove the unsupported universal “only witness” assertion; uploader-titled passages do not automatically become separate compositions or personnel credits. |
| SRC0809 | Garland film excerpt; YouTube publication 13 February 2022, not the uploader-reported 1937 music-session date or 1938 premiere. |

## Graph corrections

Film and song references now have reciprocal Source–Work, Source–Song and
Source–Film links, plus Media–Work links where the clip actually documents
both. Filmportal opening excerpts remain film-level references; no particular
song is inferred merely because it belongs to the film. The modern stage
performance remains linked to the song, not to the historical Kind Lady film.

Remove inherited sheet-music-publisher organizations from M015, M017, M022,
M025, M028 and M412; retain those publishers on their Works. The MGM studio
montage receives a reciprocal subject link to the existing MGM organization,
without claiming Kaper appears in it.

## Safeguards

`video_sources.py` preserves reviewed metadata without overwriting graph
relations. Its normalizer participates in both the canonical normalizer and
the export pipeline. Date semantics also remain explicit in `source_dates.py`.
The public graph validator now checks Source-level Work support for external
video as well as audio, and rejects inherited publisher-only video organization
links unless a source-specific production/distribution Contribution supports
that role. Tests exercise both rejected regressions and the legitimate
production-role exception.
