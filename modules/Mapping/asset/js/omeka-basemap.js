/* Basemap for this archive: self-hosted Protomaps vector tiles.
 *
 * The Mapping module drew its tiles through leaflet-providers, which meant
 * every map view fetched raster tiles from somebody else's server:
 * OpenStreetMap.Mapnik by default, with CartoDB.Positron, Esri.WorldImagery
 * and Esri.WorldShadedRelief offered in the layer control. OSM's tile CDN has
 * a usage policy that a public archive should not be leaning on, CARTO's
 * basemaps are an Enterprise product, and all three are services that can move
 * or stop. An archive should not depend on anyone staying in business.
 *
 * /basemap/protomaps-basemap.pmtiles is one self-hosted file of
 * OpenStreetMap-derived vector tiles (ODbL), served straight out of static
 * storage over HTTP range requests -- no API key, no account, no vendor. See
 * basemap/PROVENANCE.txt for how it was built and what it covers.
 *
 * It carries the world at z0-5 and the eastern and central United States at
 * z6-8. All 48 markers on this site are US theatre and recording locations
 * inside that box, and every map here opens by fitting its markers, which
 * lands around z4-z5. Above z8 the renderer over-zooms: lines and labels stay
 * sharp but no new detail appears, so MAX_ZOOM caps the controls two levels
 * past the data rather than offering zooms that only magnify.
 */
var OmekaBasemap = (function () {
    var URL = '/basemap/protomaps-basemap.pmtiles';
    var DATA_ZOOM = 8;
    var MAX_ZOOM = 10;

    return {
        maxZoom: MAX_ZOOM,
        dataZoom: DATA_ZOOM,

        addTo: function (map) {
            if (typeof protomapsL === 'undefined') {
                // The renderer is only loaded on pages that build a map; if it
                // is missing, say so rather than leaving an unexplained grey
                // box. Markers still plot, so the map is not useless.
                jQuery(map.getContainer()).append(
                    '<p class="missing-embed" style="margin:8px">The basemap could not '
                    + 'be loaded. Marker positions are still shown.</p>');
                return null;
            }
            return protomapsL.leafletLayer({
                url: URL,
                // Required. Without it the layer builds tiles and paints
                // NOTHING -- it renders vector geometry, so it needs paint
                // rules before it has anything to put on the canvas, and it
                // fails silently: tiles load, canvases stay transparent, no
                // console error. The option is `flavor`, not `theme`; passing
                // `theme` is accepted and ignored.
                flavor: 'light',
                maxDataZoom: DATA_ZOOM,
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">'
                    + 'OpenStreetMap</a> contributors'
            }).addTo(map);
        }
    };
})();
