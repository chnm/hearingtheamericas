$(document).ready( function() {

var mappingMap = $('#mapping-map');
var mappingData = mappingMap.data('mapping');

var map = L.map('mapping-map', {maxZoom: OmekaBasemap.maxZoom});
var markers = new L.FeatureGroup();

var defaultBounds = null;
if (mappingData && mappingData['o-module-mapping:bounds'] !== null) {
    var bounds = mappingData['o-module-mapping:bounds'].split(',');
    var southWest = [bounds[1], bounds[0]];
    var northEast = [bounds[3], bounds[2]];
    defaultBounds = [southWest, northEast];
}

$('.mapping-marker-popup-content').each(function() {
    var popup = $(this).clone().show();
    var latLng = new L.LatLng(popup.data('marker-lat'), popup.data('marker-lng'));
    var marker = new L.Marker(latLng);
    marker.bindPopup(popup[0]);
    markers.addLayer(marker);
});

OmekaBasemap.addTo(map);
map.addLayer(markers);
// The layer control offered four basemaps -- OpenStreetMap.Mapnik,
// CartoDB.Positron, Esri.WorldImagery and Esri.WorldShadedRelief -- all
// fetched from other people's tile servers. There is one basemap now, so a
// control that lets you choose between four copies of it would say nothing.
map.addControl(new L.Control.FitBounds(markers));

var setView = function() {
    if (defaultBounds) {
        map.fitBounds(defaultBounds);
    } else {
        var bounds = markers.getBounds();
        if (bounds.isValid()) {
            map.fitBounds(bounds);
        } else {
            map.setView([20, 0], 2)
        }
    }
};

setView();

// Switching sections changes map dimensions, so make the necessary adjustments.
$('#mapping-section').one('o:section-opened', function(e) {
    map.invalidateSize();
    setView();
});

});
