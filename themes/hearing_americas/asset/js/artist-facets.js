/* The Style facet on the Artists page.
 *
 * Omeka's FacetedBrowse module drew this list, and its facet, by three XHR
 * calls to /s/the-americas/faceted-browse/1/{categories,facets,browse} -- all
 * database queries, none of which a static host can answer. The list is in the
 * page now, and this filters it in place.
 *
 * The facet was configured with query_type "in", which is Omeka's substring
 * match, so a subject of "choro, samba" is matched by a "samba" facet value.
 * That is reproduced here rather than switched to equality, so the same
 * artists come back for the same choice as they did on the live site.
 *
 * Progressive enhancement: the fieldset is hidden until this runs, so a
 * visitor without JavaScript sees all 49 artists and no control that does
 * nothing -- which is more than the original page managed with JavaScript.
 */
(function () {
    var form = document.getElementById('artist-facets');
    var list = document.getElementById('artist-list');
    var count = document.getElementById('artist-count');
    if (!form || !list || !count) {
        return;
    }
    form.hidden = false;

    var items = Array.prototype.slice.call(list.querySelectorAll('li.resource'));

    function apply() {
        var checked = form.querySelector('input[name="style"]:checked');
        var want = checked ? checked.value : '';
        var shown = 0;
        items.forEach(function (li) {
            var subjects = li.getAttribute('data-subjects') || '';
            var match = !want || subjects.split('|').some(function (s) {
                return s.indexOf(want) !== -1;
            });
            li.hidden = !match;
            if (match) {
                shown++;
            }
        });
        count.textContent = shown === items.length
            ? shown + ' artists'
            : shown + ' of ' + items.length + ' artists';
    }

    form.addEventListener('change', apply);
    apply();
})();
