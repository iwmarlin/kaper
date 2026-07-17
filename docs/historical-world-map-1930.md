# Historical world map candidate (1930)

Status: selected and prepared for prototyping. It is not yet integrated into the
interactive map, georeferenced or converted into map tiles.

## Selected plate

The selected image is the double-hemisphere world map on pp. 2–3 of *Svensk
världsatlas*, published in Stockholm by Generalstabens litografiska anstalts
förlag in 1930. The plate is headed “Västra halvklotet” and “Östra halvklotet”,
uses Lambert equal-area azimuthal projection and gives a scale of 1:120,000,000.

- Digitized plate: <https://runeberg.org/svatlas/0010.html>
- Digitized atlas: <https://runeberg.org/svatlas/>
- LIBRIS catalogue record: <https://libris.kb.se/bib/22550149>
- Source scan retained in the repository:
  `assets/images/maps/world-1930-svensk-varldsatlas-source.jpg`
- Working copy prepared for the Atlantic presentation:
  `assets/images/maps/world-atlantic-1930-svensk-varldsatlas.jpg`

Both repository files are currently pixel-identical copies of the source scan
(3606 × 2816 px; SHA-256
`e4d4d59f6fdbe8fb518d00f23439475b7d23c81ae0a34fe2f3d8cea861e30c59`).
Keeping the working copy unaltered avoids silently changing historical map
content before the georeferencing method has been chosen.

## Suitability for the Kaper site

- It is contemporary with the archive’s 1902–1939 scope.
- It represents Europe and North America simultaneously.
- The Atlantic-facing coasts of the two hemispheres meet near the centre of the
  spread, so Kaper’s Warsaw–Berlin–Paris–Hollywood trajectory remains visually
  legible.
- Its period typography and political boundaries provide historical context
  without implying that a modern basemap is itself historical evidence.
- The source resolution is sufficient for a full-width background and moderate
  zooming.

The plate is not a Web Mercator map and must not be substituted directly for the
current OpenStreetMap tile layer. A later implementation should either use a
custom image overlay with calibrated points or a separate historical-map view.

## Atlantic presentation specification

For the first non-interactive mock-up, use the complete working image and crop it
only in the browser:

- aspect ratio: `16 / 9`;
- fit: `cover`;
- position: `center top`;
- preserve the full image in the record/detail view;
- do not bake labels, routes or markers into the JPEG.

This creates an Atlantic-oriented viewport without deleting the headings,
legend or marginal evidence from the archival master. The exact visible crop
can be adjusted responsively without producing another derivative file.

## Rights and provenance assessment

The atlas title, publisher and 1930 publication date are supported by the
digitized volume and the LIBRIS catalogue record. No individual cartographer is
credited on the selected plate. Project Runeberg provides the scanned atlas
openly. Wikimedia Commons also treats an analogous 1930 Europe plate from the
same atlas, with an unidentified cartographer, as public domain:
<https://commons.wikimedia.org/wiki/File:Europa_map_1930,_svatlas.jpg>.

The working status for this project is therefore **public domain according to
the available source-family documentation**, with full attribution retained.
This is an evidence-based rights assessment, not a claim that every jurisdiction
applies identical rules. The public record should identify the atlas, publisher,
date, plate, digitizing source and source URL rather than using an unqualified
“copyright free” label.

Recommended credit line:

> *Svensk världsatlas*, Generalstabens litografiska anstalts förlag, Stockholm,
> 1930, pp. 2–3, digitized by Project Runeberg. Public-domain assessment based on
> the available source documentation.

