/* Browser-style page tabs under the navbar.
 *
 * - A link clicked in the top menu opens as a NEW tab (or jumps to the tab
 *   already showing that exact page).
 * - Anything else (links inside a page, saving a form, Back) stays in the
 *   current tab, the way a browser tab works.
 * - Tabs stay until closed with x; they are kept in this browser per user.
 *   Switching tab re-opens that page (its saved URL). The Job Sheet's Expense
 *   and Fuel sections keep their unsaved typing themselves (see job_sheet.html).
 */
(function () {
    var bar = document.getElementById('appTabs');
    if (!bar) return;
    var KEY = 'amTabs:' + (bar.dataset.user || '');
    var MAX_TABS = 15;

    function get(store, k) { try { return store.getItem(k); } catch (e) { return null; } }
    function set(store, k, v) { try { store.setItem(k, v); } catch (e) { /* storage blocked */ } }
    function del(store, k) { try { store.removeItem(k); } catch (e) { /* storage blocked */ } }
    function loadTabs() { try { return JSON.parse(get(localStorage, KEY)) || []; } catch (e) { return []; } }
    function saveTabs(t) { set(localStorage, KEY, JSON.stringify(t)); }
    function setIntent(kind, id) { set(sessionStorage, 'amTabIntent', JSON.stringify({ kind: kind, id: id || '', at: Date.now() })); }
    function takeIntent() {
        var raw = get(sessionStorage, 'amTabIntent');
        del(sessionStorage, 'amTabIntent');
        try {
            var i = JSON.parse(raw);
            return i && Date.now() - i.at < 15000 ? i : null;   // ignore stale (e.g. a download link)
        } catch (e) { return null; }
    }
    function newId() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 6); }

    // This page's title: data-tab-title, else the page heading, else <title>
    var url = location.pathname + location.search;
    var head = document.querySelector('.content-area [data-tab-title]') ||
               document.querySelector('.content-area h1, .content-area h2, .content-area h3');
    var title = head ? (head.getAttribute('data-tab-title') || head.textContent) : document.title.split('|')[0];
    title = (title || 'Page').replace(/\s+/g, ' ').trim();

    var tabs = loadTabs();
    var activeId = get(sessionStorage, 'amActiveTab');
    var intent = takeIntent();
    var current = null;
    var find = function (fn) { for (var i = 0; i < tabs.length; i++) if (fn(tabs[i])) return tabs[i]; return null; };

    if (intent && intent.kind === 'switch') current = find(function (t) { return t.id === intent.id; });
    if (!current && intent && intent.kind === 'new') {
        current = find(function (t) { return t.url === url; });
        if (!current) { current = { id: newId() }; tabs.push(current); }
    }
    if (!current) current = find(function (t) { return t.id === activeId; });
    if (!current) {
        current = find(function (t) { return t.url === url; });
        if (!current) { current = { id: newId() }; tabs.push(current); }
    }
    current.url = url;
    current.title = title;
    while (tabs.length > MAX_TABS) {
        var drop = tabs[0] === current ? 1 : 0;
        tabs.splice(drop, 1);
    }
    saveTabs(tabs);
    set(sessionStorage, 'amActiveTab', current.id);

    function render() {
        bar.innerHTML = '';
        tabs.forEach(function (t) {
            var tab = document.createElement('div');
            tab.className = 'app-tab' + (t.id === current.id ? ' active' : '');
            tab.title = t.title;
            var a = document.createElement('a');
            a.href = t.url;
            a.textContent = t.title;
            a.addEventListener('click', function (e) {
                if (e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0) return;
                if (t.id === current.id) { e.preventDefault(); return; }
                setIntent('switch', t.id);
            });
            tab.appendChild(a);
            if (tabs.length > 1) {
                var x = document.createElement('button');
                x.type = 'button';
                x.className = 'app-tab-close';
                x.setAttribute('aria-label', 'Close tab');
                x.innerHTML = '&times;';
                x.addEventListener('click', function (e) {
                    e.preventDefault();
                    var i = tabs.indexOf(t);
                    tabs.splice(i, 1);
                    saveTabs(tabs);
                    if (t.id === current.id) {
                        var next = tabs[i] || tabs[i - 1];
                        setIntent('switch', next.id);
                        location.href = next.url;
                    } else {
                        render();
                    }
                });
                tab.appendChild(x);
            }
            bar.appendChild(tab);
        });
        var plus = document.createElement('a');
        plus.className = 'app-tab-new';
        plus.href = bar.dataset.home || '/';
        plus.title = 'New tab';
        plus.innerHTML = '<i class="bi bi-plus-lg"></i>';
        plus.addEventListener('click', function () { setIntent('new'); });
        bar.appendChild(plus);
        var act = bar.querySelector('.app-tab.active');
        if (act && act.scrollIntoView) act.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    }
    render();

    // Top-menu links open as a new tab
    document.querySelectorAll('.app-navbar a[href]').forEach(function (a) {
        if (bar.contains(a) || a.hasAttribute('data-bs-toggle') || a.target === '_blank') return;
        var href = a.getAttribute('href');
        if (!href || href.charAt(0) === '#' || /^(javascript|mailto|tel):/i.test(href) || /logout/i.test(href)) return;
        a.addEventListener('click', function (e) {
            if (e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0) return;
            setIntent('new');
        });
    });

    // Another browser window changed the tabs - keep this bar in step
    window.addEventListener('storage', function (e) {
        if (e.key !== KEY) return;
        var fresh = loadTabs();
        var still = null;
        for (var i = 0; i < fresh.length; i++) if (fresh[i].id === current.id) still = fresh[i];
        if (!still) { fresh.push(current); saveTabs(fresh); }
        tabs = fresh;
        render();
    });
})();
