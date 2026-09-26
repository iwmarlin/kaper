# Historical basemap implementation

The public map uses a calibrated historical overview and a separate present-day
geographic reference at closer zoom levels. Markers and routes remain geographic
Leaflet layers throughout the transition and therefore do not move when the
basemap changes.

## Historical overview

- Edward Stanford Ltd., *The World on Mercator's Projection*, 1926.
- Published in *Stanford's London Atlas of Universal Geography*, “Whitehall”
  edition.
- David Rumsey Map Collection list number 14508.007:
  <https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~363901~90131510%3AThe-world-on-Mercator-s-projection->
- Public-domain file record:
  <https://commons.wikimedia.org/wiki/File:The_world_(Mercator),_1926.jpg>
- Display derivative:
  `assets/images/maps/world-1926-stanford-mercator.jpg`

The display derivative removes the atlas-page margins but does not alter the
cartographic content. It is 2400 × 1724 pixels and has SHA-256
`e7bf78c3018888bb7d3b81df410931a63874c47fbb2c984d4d6e4199285152d7`.

The source is a continuous Mercator map with a longitude and latitude graticule.
The calibrated image bounds used by Leaflet are:

```text
south: -70.1
west: -195.5
north: 84.5
east: 183.2
```

The longitude range extends beyond −180° because the retained derivative still
contains the printed map border outside the −180° graticule. This keeps the
interior meridians and the public place markers aligned.

## Zoom transition

- zoom 3 and below: historical map only;
- zoom 4: historical map and present-day reference cross-fade;
- zoom 5 and above: present-day geographic reference only.

These thresholds follow the display derivative rather than preference: at zoom 3
the plate is shown at its native resolution, and each further level doubles the
magnification of a scan that is stretched to a single bounding rectangle, not
warped to control points. Holding it longer would show a blurred plate drifting
away from the markers.

Choosing a cluster or a place zooms past zoom 5 in one step, so the map carries
a “Whole route” control under the zoom buttons. It returns to the opening view
of the documented route, never closer than zoom 3, where the historical plate is
sharp again, and it leaves any selected place selected.

The close-range layer is explicitly labelled “Present-day geographic reference”.
It is supplied for address legibility and must not be described as a
reconstruction of the historical street network.

## Attribution

Historical view:

> Edward Stanford Ltd., *The World on Mercator's Projection*, 1926. David Rumsey
> Map Collection, David Rumsey Map Center, Stanford University Libraries.

Reference view:

> © OpenStreetMap contributors.

The active attribution changes with the visible layer. Both attributions are
shown during the cross-fade.

