/* Slideshow behaviour for the timeline.
 *
 * The slides are already in the page -- index.html is generated from
 * timeline.json at build time -- so this script's whole job is to turn a
 * readable stack of twenty sections into one-at-a-time with a navigation
 * strip. If it never runs, the timeline is still there and still readable,
 * which is more than the library it replaces managed.
 *
 * Every marker's year and headline come from data- attributes on the slides,
 * so this file holds no content and the two cannot drift apart.
 */
(function () {
    var root = document.querySelector('.tl');
    if (!root) return;

    var slides = Array.prototype.slice.call(root.querySelectorAll(".tl-slide"));
    if (slides.length < 2) return;

    var YEARS = slides
        .map(function (s) { return parseInt(s.getAttribute('data-year'), 10); })
        .filter(function (y) { return !isNaN(y); });
    var MIN = Math.min.apply(null, YEARS);
    var MAX = Math.max.apply(null, YEARS);
    var SPAN = MAX - MIN || 1;

    /* ---------------------------------------------------------------- nav */

    var nav = document.createElement('nav');
    nav.className = 'tl-nav';
    nav.setAttribute('aria-label', 'Timeline events');

    var prev = document.createElement('button');
    prev.type = 'button';
    prev.className = 'tl-step tl-prev';
    prev.innerHTML = '‹';
    prev.setAttribute('aria-label', 'Previous event');

    var next = document.createElement('button');
    next.type = 'button';
    next.className = 'tl-step tl-next';
    next.innerHTML = '›';
    next.setAttribute('aria-label', 'Next event');

    var track = document.createElement('div');
    track.className = 'tl-track';

    // One lane per group, earliest group first, so the strip reads left to
    // right in time. Ordering by first mention would put the title slide's
    // group first, which is whichever one the spreadsheet happened to name.
    var firstYear = {};
    slides.forEach(function (s) {
        var g = s.getAttribute('data-group');
        var y = parseInt(s.getAttribute('data-year'), 10);
        if (!g || isNaN(y)) return;
        if (firstYear[g] === undefined || y < firstYear[g]) firstYear[g] = y;
    });

    var lanes = {};
    Object.keys(firstYear)
        .sort(function (a, b) { return firstYear[a] - firstYear[b]; })
        .forEach(function (g) {
            var lane = document.createElement('div');
            lane.className = 'tl-lane';
            var name = document.createElement('span');
            name.className = 'tl-lane-name';
            name.textContent = g;
            lane.appendChild(name);
            lanes[g] = lane;
            track.appendChild(lane);
        });

    var markers = [];
    slides.forEach(function (slide, i) {
        var year = parseInt(slide.getAttribute('data-year'), 10);
        var group = slide.getAttribute('data-group');
        if (isNaN(year) || !lanes[group]) return;   // the title slide has neither

        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'tl-marker';
        b.style.left = ((year - MIN) / SPAN * 100) + '%';
        // The dot carries no visible text, so the accessible name is the whole
        // label: four events share 1917 and "1917" alone would not tell them
        // apart in a list of controls.
        b.setAttribute('aria-label',
            slide.getAttribute('data-display-date') + ': ' + slide.getAttribute('data-headline'));
        b.addEventListener('click', function () { show(i, b); });
        b.addEventListener('mouseenter', function () { readout(i); });
        b.addEventListener('focus', function () { readout(i); });
        b.addEventListener('mouseleave', function () { readout(current); });
        b.addEventListener('blur', function () { readout(current); });
        lanes[group].appendChild(b);
        markers.push({ index: i, el: b, year: year, group: group });
    });

    /* Four events share 1917 and two each share 1912 and 1920. Stacked at the
     * same x they cover one another: only the last one drawn is clickable, and
     * the touch targets overlap. Pack each lane into as many rows as it needs,
     * keeping every marker at its true date and no two within PITCH pixels of
     * each other horizontally on the same row. PITCH is the touch target, so
     * the rows also satisfy the spacing half of 2.5.8.
     */
    var PITCH = 28;
    var ROW = 28;

    function packLanes() {
        var width = track.clientWidth;
        if (!width) return;
        Object.keys(lanes).forEach(function (g) {
            var mine = markers.filter(function (m) { return m.group === g; })
                              .sort(function (a, b) { return a.year - b.year; });
            var lastInRow = [];
            mine.forEach(function (m) {
                var x = (m.year - MIN) / SPAN * width;
                var r = 0;
                while (lastInRow[r] !== undefined && x - lastInRow[r] < PITCH) r++;
                lastInRow[r] = x;
                m.el.style.top = (12 + r * ROW) + 'px';
            });
            lanes[g].style.height = (12 + Math.max(1, lastInRow.length) * ROW) + 'px';
        });
    }

    // Decade ticks across whatever span the data turns out to cover.
    var axis = document.createElement('div');
    axis.className = 'tl-axis';
    for (var y = Math.ceil(MIN / 10) * 10; y <= MAX; y += 10) {
        var t = document.createElement('span');
        t.className = 'tl-tick';
        t.style.left = ((y - MIN) / SPAN * 100) + '%';
        t.textContent = y;
        t.setAttribute('aria-hidden', 'true');   // the dates are on the slides
        axis.appendChild(t);
    }
    track.appendChild(axis);

    /* A jump-to-event control for narrow viewports.
     *
     * The lane strip needs 28px between markers to keep their touch targets
     * 24px apart, and the narrower the track the more events collide into
     * extra rows: at 320px the strip grows to 375px tall and pushes itself out
     * of the 650px frame the home page gives it. Below 700px the strip is
     * replaced by this, which reaches every event in one control and costs one
     * line of height. It stays in the DOM at every width so the two never get
     * out of step.
     */
    var jump = document.createElement('select');
    jump.className = 'tl-jump';
    jump.setAttribute('aria-label', 'Jump to an event');
    slides.forEach(function (slide, i) {
        var o = document.createElement('option');
        o.value = i;
        var d = slide.getAttribute('data-display-date');
        o.textContent = (d ? d + ' — ' : '') + slide.getAttribute('data-headline');
        jump.appendChild(o);
    });
    jump.addEventListener('change', function () { show(parseInt(jump.value, 10)); });

    nav.appendChild(prev);
    nav.appendChild(track);
    nav.appendChild(jump);
    nav.appendChild(next);

    var read = document.createElement('p');
    read.className = 'tl-readout';
    read.setAttribute('aria-hidden', 'true');    // duplicates the slide heading

    root.appendChild(nav);
    root.appendChild(read);

    /* ------------------------------------------------------------ showing */

    var current = -1;

    function readout(i) {
        var s = slides[i];
        if (!s) { read.textContent = ''; return; }
        var d = s.getAttribute('data-display-date');
        read.innerHTML = '';
        if (d) {
            var b = document.createElement('b');
            b.textContent = d;
            read.appendChild(b);
            read.appendChild(document.createTextNode('  '));
        }
        read.appendChild(document.createTextNode(s.getAttribute('data-headline') || ''));
    }

    function show(i, keepFocusOn) {
        if (i < 0 || i >= slides.length || i === current) return;
        current = i;
        slides.forEach(function (s, n) {
            s.hidden = n !== i;
        });
        markers.forEach(function (m) {
            if (m.index === i) m.el.setAttribute('aria-current', 'true');
            else m.el.removeAttribute('aria-current');
        });
        prev.disabled = i === 0;
        next.disabled = i === slides.length - 1;
        if (jump.value !== String(i)) jump.value = String(i);
        readout(i);
        if (keepFocusOn && document.activeElement !== keepFocusOn) keepFocusOn.focus();
    }

    prev.addEventListener('click', function () { show(current - 1, prev.disabled ? null : prev); });
    next.addEventListener('click', function () { show(current + 1, next.disabled ? null : next); });

    root.addEventListener('keydown', function (e) {
        if (e.altKey || e.ctrlKey || e.metaKey) return;
        var k = e.key;
        if (k === 'ArrowLeft') { show(current - 1); }
        else if (k === 'ArrowRight') { show(current + 1); }
        else if (k === 'Home') { show(0); }
        else if (k === 'End') { show(slides.length - 1); }
        else return;
        e.preventDefault();
    });

    root.classList.add('tl--js');
    show(0);
    packLanes();

    if (window.ResizeObserver) {
        new ResizeObserver(packLanes).observe(track);
    } else {
        window.addEventListener('resize', packLanes);
    }
})();
