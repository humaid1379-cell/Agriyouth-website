/* ===== NABD AI — DOCUMENT RENDERER =====
   Renders Part II (Gantt + component tables) and the Section 8 mapping table
   from roadmap-data.js. Every total is computed here rather than authored, so
   the published plan cannot disagree with itself.
*/

(function () {
    'use strict';

    /* Acceptance criteria that Section 8 adds to sub-tasks already in the plan.
       Keyed by task id; each entry costs zero additional hours. */
    const S8_DIRECTIVES = {
        '1.3.1': 'Emit the coarse block (route, risk band, output class, reviewer requirement, gate flags) under constrained decoding <em>before</em> any draft prose, and hash it.',
        '1.3.2': 'Verifier accuracy is measured against a versioned corpus of captured Stage&nbsp;1 outputs with their failure modes intact — never against hand-written clean drafts.',
        '1.3.3': 'Refiner receives the coarse block as read-only context. It may emit fine detail only; the packet fails to serialize if <code>sha256(coarse_block)</code> changes.',
        '2.2.1': 'Risk bands are the coarse unit. Sub-scores are expressed inside a band and carry no authority to change the band label.',
        '2.2.3': 'Runs before any model call and is the sole writer of the band. Downgrades are unreachable; upgrades require a deterministic re-run.',
        '2.3.2': 'Also fires when a downstream stage attempts to alter a locked coarse decision, routing to <code>MORE_EVIDENCE</code> or <code>BLOCKED</code>.',
        '3.2.2': 'Serialize and hash the coarse block separately from fine detail so the decision can be verified without parsing prose.',
        '5.2.2': 'Pilot cases are replayed from captured Stage&nbsp;1 drafts, including injection, mis-parse and dropped-mandate failures.',
        '5.2.3': 'Budget the coarse call as a small constrained generation on a cheaper tier; concentrate spend on the fine pass.'
    };

    const HPD = ROADMAP.hoursPerDay;

    /* ---------------------------------------------------------- formatting */

    // Sub-task day figures keep a trailing zero on whole days: 8h -> "1.0d".
    function taskDays(h) {
        const d = h / HPD;
        return Number.isInteger(d) ? d.toFixed(1) : String(parseFloat(d.toFixed(3)));
    }

    // Rollup day figures drop it: 40h -> "5 Days", 52h -> "6.5 Days".
    function rollupDays(h) {
        const d = h / HPD;
        return Number.isInteger(d) ? String(d) : String(parseFloat(d.toFixed(2)));
    }

    function sum(items, key) {
        return items.reduce((total, item) => total + item[key], 0);
    }

    function componentTotals(component) {
        const base = sum(component.tasks, 'base');
        const buffer = sum(component.tasks, 'buffer');
        return { base: base, buffer: buffer, total: base + buffer };
    }

    function layerTotals(layer) {
        return layer.components.reduce(function (acc, component) {
            const t = componentTotals(component);
            acc.base += t.base;
            acc.buffer += t.buffer;
            acc.total += t.total;
            return acc;
        }, { base: 0, buffer: 0, total: 0 });
    }

    const totals = ROADMAP.layers.map(layerTotals);
    const grand = totals.reduce(function (acc, t) {
        acc.base += t.base;
        acc.buffer += t.buffer;
        acc.total += t.total;
        return acc;
    }, { base: 0, buffer: 0, total: 0 });

    // Layer 5 is the testing effort, not a deployed component: the runtime count
    // is what sub-task 5.2.1 packages.
    const runtimeComponents = ROADMAP.layers.reduce(function (n, l) {
        return l.runtime ? n + l.components.length : n;
    }, 0);
    const trackWeeks = grand.total / ROADMAP.hoursPerWeek;

    /* ---------------------------------------------------------------- gantt */

    function renderGantt() {
        const host = document.getElementById('ganttChart');
        if (!host) return;

        let weekCells = '';
        for (let w = 1; w <= ROADMAP.weeks; w++) {
            weekCells += '<div class="gantt-week"><b>W' + w + '</b> (' + ROADMAP.hoursPerWeek + 'h)</div>';
        }

        let html =
            '<div class="gantt-row gantt-row--head">' +
                '<div class="gantt-cell-label">Architectural Layer</div>' +
                '<div class="gantt-weeks">' + weekCells + '</div>' +
            '</div>';

        let cursor = 0;
        ROADMAP.layers.forEach(function (layer, i) {
            const t = totals[i];
            const left = (cursor / grand.total) * 100;
            const baseW = (t.base / grand.total) * 100;
            const bufW = (t.buffer / grand.total) * 100;
            cursor += t.total;

            // Narrow buffer segments drop the word "Buf" so the figure stays legible.
            const bufLabel = bufW >= 6 ? '+' + t.buffer + 'h Buf' : '+' + t.buffer + 'h';

            html +=
                '<div class="gantt-row">' +
                    '<div class="gantt-cell-label">' +
                        '<span class="gantt-dot" style="background:var(--' + layer.accent + ')"></span>' +
                        layer.ganttLabel +
                    '</div>' +
                    '<div class="gantt-track">' +
                        '<div class="gantt-bar" data-accent="' + layer.accent + '" ' +
                             'style="left:' + left.toFixed(4) + '%;width:' + (baseW + bufW).toFixed(4) + '%">' +
                            '<div class="gantt-base" style="flex:' + t.base + ' 0 0">' + t.base + 'h Base</div>' +
                            '<div class="gantt-buf" style="flex:' + t.buffer + ' 0 0">' + bufLabel + '</div>' +
                        '</div>' +
                    '</div>' +
                '</div>';
        });

        host.innerHTML = html;
    }

    /* --------------------------------------------------------------- layers */

    function taskRow(task) {
        const flag = task.s8 ? ' <span class="s8-flag">&sect;8</span>' : '';
        const stack = task.stack.map(function (s) {
            return '<span class="stack-pill">' + s + '</span>';
        }).join('');

        return '<tr>' +
            '<td class="t-id"><span>' + task.id + '</span></td>' +
            '<td class="t-name"><strong>' + task.name + flag + '</strong><p>' + task.desc + '</p></td>' +
            '<td class="t-stack">' + stack + '</td>' +
            '<td class="t-base">' + task.base + 'h (' + taskDays(task.base) + 'd)</td>' +
            '<td class="t-buf">+' + task.buffer + 'h</td>' +
            '<td class="t-deliv"><span class="deliv-pill">' + task.deliverable + '</span></td>' +
        '</tr>';
    }

    function componentBlock(component) {
        const t = componentTotals(component);
        const anchor = 'c-' + component.id.replace(/\./g, '-');

        return '<div class="comp-head" id="' + anchor + '">' +
                '<h3 class="comp-title">' + component.id + ' ' + component.name +
                    ' <span>&mdash; ' + component.tagline + '</span></h3>' +
                '<p class="comp-total">Base: <b>' + t.base + 'h</b> | Buffer: <b>+' + t.buffer + 'h</b> | ' +
                    'Total: <b>' + t.total + ' Hours</b> (' + rollupDays(t.total) + ' Days)</p>' +
            '</div>' +
            '<div class="task-wrap"><table class="task-table">' +
                '<thead><tr>' +
                    '<th scope="col">ID</th>' +
                    '<th scope="col">Sub-task name &amp; technical description</th>' +
                    '<th scope="col">Target tech stack</th>' +
                    '<th scope="col">Base hours</th>' +
                    '<th scope="col">Buffer hours</th>' +
                    '<th scope="col">Deliverable</th>' +
                '</tr></thead>' +
                '<tbody>' + component.tasks.map(taskRow).join('') + '</tbody>' +
            '</table></div>';
    }

    function renderLayers() {
        const host = document.getElementById('layers');
        if (!host) return;

        host.innerHTML = ROADMAP.layers.map(function (layer, i) {
            const t = totals[i];
            return '<section class="layer-sec" id="layer-' + layer.id + '" data-accent="' + layer.accent + '">' +
                    '<header class="layer-head">' +
                        '<h2>' + layer.id + '. ' + layer.title + '</h2>' +
                        '<p class="layer-total">Base: ' + t.base + ' Hours | Buffer: ' + t.buffer + ' Hours | ' +
                            'Total: ' + t.total + ' Hours (' + rollupDays(t.total) + ' Working Days)</p>' +
                    '</header>' +
                    layer.components.map(componentBlock).join('') +
                '</section>';
        }).join('');
    }

    /* ------------------------------------------------------ section 8 table */

    function renderS8Map() {
        const body = document.querySelector('#s8MapTable tbody');
        if (!body) return;

        let rows = '';
        ROADMAP.layers.forEach(function (layer) {
            layer.components.forEach(function (component) {
                component.tasks.forEach(function (task) {
                    if (!task.s8) return;
                    rows += '<tr>' +
                        '<th scope="row">' + task.id + '</th>' +
                        '<td>' + task.name + '</td>' +
                        '<td>' + (S8_DIRECTIVES[task.id] || task.desc) + '</td>' +
                    '</tr>';
                });
            });
        });

        body.innerHTML = rows;
    }

    /* -------------------------------------------------------- derived chips */

    function renderHeaderFigures() {
        const hoursChip = document.getElementById('chipHours');
        const compChip = document.getElementById('chipComponents');
        const ganttTitle = document.getElementById('ganttTitle');
        const s8Budget = document.getElementById('s8Budget');

        if (hoursChip) hoursChip.textContent = grand.total + ' Hours';
        if (compChip) compChip.textContent = runtimeComponents + ' Components';
        if (ganttTitle) {
            ganttTitle.textContent = trackWeeks + '-Week Strategic Visual Gantt Roadmap (' +
                grand.total + ' Hours Timeline)';
        }
        if (s8Budget) s8Budget.textContent = '0 additional hours against the ' + grand.total + '-hour envelope';
    }

    /* ------------------------------------------------------------ contents */

    function initContents() {
        const links = Array.prototype.slice.call(
            document.querySelectorAll('.toc-nav a[href^="#"]')
        );

        const entries = links.map(function (link) {
            return { link: link, target: document.getElementById(link.getAttribute('href').slice(1)) };
        }).filter(function (e) { return e.target; });

        if (!entries.length) return;

        let ticking = false;
        let current = null;

        function highlight() {
            ticking = false;

            let active = entries[0];
            for (let i = 0; i < entries.length; i++) {
                if (entries[i].target.getBoundingClientRect().top <= 130) {
                    active = entries[i];
                } else {
                    break;
                }
            }

            // Bottom of page: the last entry wins regardless of offset.
            if (window.innerHeight + window.scrollY >= document.body.scrollHeight - 4) {
                active = entries[entries.length - 1];
            }

            if (active === current) return;
            current = active;

            links.forEach(function (l) { l.classList.remove('active', 'parent-active'); });
            active.link.classList.add('active');

            const parentItem = active.link.closest('ul ul');
            if (parentItem) {
                const parentLink = parentItem.parentElement.querySelector(':scope > a');
                if (parentLink) parentLink.classList.add('parent-active');
            }
        }

        function onScroll() {
            if (ticking) return;
            ticking = true;
            window.requestAnimationFrame(highlight);
        }

        window.addEventListener('scroll', onScroll, { passive: true });
        window.addEventListener('resize', onScroll, { passive: true });
        highlight();
    }

    function initDrawer() {
        const toggle = document.getElementById('tocToggle');
        const toc = document.getElementById('toc');
        const scrim = document.getElementById('tocScrim');
        if (!toggle || !toc || !scrim) return;

        function setOpen(open) {
            toc.classList.toggle('open', open);
            scrim.hidden = !open;
            toggle.setAttribute('aria-expanded', String(open));
            document.body.style.overflow = open ? 'hidden' : '';
        }

        toggle.addEventListener('click', function () {
            setOpen(toggle.getAttribute('aria-expanded') !== 'true');
        });
        scrim.addEventListener('click', function () { setOpen(false); });
        toc.addEventListener('click', function (e) {
            if (e.target.closest('a')) setOpen(false);
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') setOpen(false);
        });
    }

    /* ------------------------------------------------------------ bootstrap */

    function init() {
        renderGantt();
        renderLayers();
        renderS8Map();
        renderHeaderFigures();
        initDrawer();
        initContents();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
