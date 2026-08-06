(function () {
    'use strict';

    // Back to top
    var topBtn = document.getElementById('backToTop');
    if (topBtn) {
        window.addEventListener('scroll', function () {
            topBtn.style.display = window.scrollY > 300 ? 'block' : 'none';
        });
        topBtn.addEventListener('click', function () {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // Generic table search helper
    window.initTableSearch = function (inputId, tableBodyId) {
        var input = document.getElementById(inputId);
        var tbody = document.getElementById(tableBodyId);
        if (!input || !tbody) return;

        input.addEventListener('input', function () {
            var q = input.value.toLowerCase();
            tbody.querySelectorAll('tr').forEach(function (row) {
                row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
            });
        });
    };

    // Turns any <select class="searchable-select"> into a type-to-search field
    // backed by a native <datalist>. The original <select> stays in the form
    // (hidden) and keeps submitting normally, so no other code has to change.
    function enhanceSearchableSelect(select) {
        if (!select || select.dataset.enhanced) return;
        select.dataset.enhanced = '1';

        var options = Array.prototype.slice.call(select.options);
        var listId = (select.id || 'searchable-' + Math.random().toString(36).slice(2)) + '-options';

        var datalist = document.createElement('datalist');
        datalist.id = listId;
        options.forEach(function (opt) {
            if (!opt.value) return;
            var dOpt = document.createElement('option');
            dOpt.value = opt.textContent;
            datalist.appendChild(dOpt);
        });

        var textInput = document.createElement('input');
        textInput.type = 'text';
        textInput.className = select.className;
        textInput.setAttribute('list', listId);
        textInput.setAttribute('placeholder', 'Type to search...');
        textInput.setAttribute('autocomplete', 'off');

        var selected = options.filter(function (o) { return o.selected && o.value; })[0];
        textInput.value = selected ? selected.textContent : '';

        // The original <select> is what carries autofocus (if this field is
        // meant to be the form's starting field) - but it's about to be
        // hidden below, so the browser's autofocus would land on nothing.
        // Hand focus to the replacement text input instead.
        if (select.hasAttribute('autofocus')) {
            textInput.setAttribute('autofocus', 'autofocus');
            setTimeout(function () { textInput.focus(); }, 0);
        }

        select.style.display = 'none';
        select.insertAdjacentElement('beforebegin', textInput);
        select.insertAdjacentElement('beforebegin', datalist);

        function syncFromText() {
            var match = options.filter(function (o) { return o.textContent === textInput.value; })[0];
            if (match) {
                select.value = match.value;
            } else if (!textInput.value) {
                select.value = '';
            }
            select.dispatchEvent(new Event('change', { bubbles: true }));
        }

        textInput.addEventListener('input', syncFromText);
        textInput.addEventListener('change', syncFromText);
        // One click selects whatever name is already there, so typing
        // immediately replaces it instead of the user having to delete first.
        textInput.addEventListener('focus', function () {
            textInput.select();
        });
    }

    window.enhanceSearchableSelects = function () {
        document.querySelectorAll('select.searchable-select').forEach(enhanceSearchableSelect);
    };

    // Turns a <select class="dropdown-search-select"> into a proper live
    // search dropdown (dark, prefix-matched) - used where a native <datalist>
    // isn't precise/visible enough, e.g. the Route picker in Client Rates.
    // Only options whose text STARTS WITH the typed query are shown (not a
    // "contains anywhere" match), so typing "khi" only surfaces routes
    // starting at KHI, not ones that merely end in KHI.
    function enhanceDropdownSearchSelect(select) {
        if (!select || select.dataset.enhanced) return;
        select.dataset.enhanced = '1';

        var options = Array.prototype.slice.call(select.options).filter(function (o) { return o.value; });

        var wrapper = document.createElement('div');
        wrapper.className = 'dropdown-search-wrapper';

        var textInput = document.createElement('input');
        textInput.type = 'text';
        textInput.className = 'form-control dropdown-search-input';
        textInput.setAttribute('placeholder', select.dataset.placeholder || 'Type to search...');
        textInput.setAttribute('autocomplete', 'off');

        var list = document.createElement('div');
        list.className = 'dropdown-search-list';

        var selected = options.filter(function (o) { return o.selected; })[0];
        textInput.value = selected ? selected.textContent.trim() : '';

        if (select.hasAttribute('autofocus')) {
            textInput.setAttribute('autofocus', 'autofocus');
            setTimeout(function () { textInput.focus(); }, 0);
        }

        select.style.display = 'none';
        select.insertAdjacentElement('beforebegin', wrapper);
        wrapper.appendChild(textInput);
        wrapper.appendChild(list);
        wrapper.appendChild(select);

        var activeIndex = -1;

        function renderList() {
            var q = textInput.value.trim().toUpperCase();
            var matches = q ? options.filter(function (o) { return o.textContent.trim().toUpperCase().indexOf(q) === 0; }) : options;
            list.innerHTML = '';
            activeIndex = -1;
            if (!matches.length) {
                var empty = document.createElement('div');
                empty.className = 'dropdown-search-empty';
                empty.textContent = 'No matching route';
                list.appendChild(empty);
            } else {
                matches.forEach(function (opt) {
                    var item = document.createElement('div');
                    item.className = 'dropdown-search-item';
                    item.textContent = opt.textContent.trim();
                    item.dataset.value = opt.value;
                    item.addEventListener('mousedown', function (e) {
                        e.preventDefault();
                        select.value = opt.value;
                        textInput.value = opt.textContent.trim();
                        closeList();
                        select.dispatchEvent(new Event('change', { bubbles: true }));
                    });
                    list.appendChild(item);
                });
            }
            list.classList.add('show');
        }

        function closeList() {
            list.classList.remove('show');
            list.innerHTML = '';
            activeIndex = -1;
        }

        function setActive(idx) {
            var items = list.querySelectorAll('.dropdown-search-item');
            items.forEach(function (el) { el.classList.remove('active'); });
            if (idx >= 0 && idx < items.length) {
                items[idx].classList.add('active');
                items[idx].scrollIntoView({ block: 'nearest' });
            }
            activeIndex = idx;
        }

        textInput.addEventListener('input', function () {
            if (!textInput.value) {
                select.value = '';
                select.dispatchEvent(new Event('change', { bubbles: true }));
            }
            renderList();
        });
        textInput.addEventListener('focus', function () {
            textInput.select();
            renderList();
        });
        textInput.addEventListener('blur', function () {
            setTimeout(closeList, 150);
        });
        textInput.addEventListener('keydown', function (e) {
            var items = list.querySelectorAll('.dropdown-search-item');
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (!items.length) return;
                setActive(Math.min(activeIndex + 1, items.length - 1));
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (!items.length) return;
                setActive(Math.max(activeIndex - 1, 0));
            } else if (e.key === 'Enter') {
                if (activeIndex > -1 && items[activeIndex]) {
                    e.preventDefault();
                    items[activeIndex].dispatchEvent(new Event('mousedown'));
                }
            } else if (e.key === 'Escape') {
                closeList();
            }
        });
    }

    window.enhanceDropdownSearchSelects = function () {
        document.querySelectorAll('select.dropdown-search-select').forEach(enhanceDropdownSearchSelect);
    };

    // Turns any <input class="datepicker"> into a typing-friendly date field
    // showing "10-Jan-26" (Flatpickr's altInput), while the real value
    // submitted to the server stays ISO (Y-m-d) so Django's DateField parses
    // it normally. Empty fields default to today's date on load; add
    // data-max-today="1" on a field to cap it at today (e.g. a job date that
    // can't be in the future). flatpickr is bundled locally (static/vendor/)
    // instead of a CDN so it can't go stale behind a caching layer.
    window.enhanceDatepickers = function () {
        if (typeof flatpickr === 'undefined') return;
        document.querySelectorAll('input.datepicker').forEach(function (el) {
            if (el.dataset.fpEnhanced) return;
            el.dataset.fpEnhanced = '1';

            // Wrap the input so a calendar icon can sit inside it - makes it
            // visually obvious this is a date picker, not a plain text box.
            var wrapper = document.createElement('div');
            wrapper.className = 'datepicker-wrapper';
            el.parentNode.insertBefore(wrapper, el);
            wrapper.appendChild(el);

            var opts = {
                dateFormat: 'Y-m-d',
                altInput: true,
                altFormat: 'd-M-y',
                allowInput: true,
                locale: { firstDayOfWeek: 1 },
                onReady: function (selectedDates, dateStr, instance) {
                    var icon = document.createElement('i');
                    icon.className = 'bi bi-calendar3 datepicker-icon';
                    icon.addEventListener('click', function () {
                        instance.open();
                    });
                    wrapper.appendChild(icon);

                    // Typing into a field that already shows a date (e.g.
                    // today's default) inserted new characters into the
                    // middle of the existing text instead of replacing it,
                    // garbling the value and making flatpickr land on the
                    // wrong date. Select the existing text on focus so any
                    // typing cleanly replaces it.
                    instance.altInput.addEventListener('focus', function () {
                        instance.altInput.select();
                    });
                },
                // Closing the calendar (date picked, Escape, or click-away)
                // leaves nothing focused, so the next Tab press restarted
                // from the very first focusable element on the page (the
                // navbar logo) instead of continuing in the form. Hand focus
                // to the next real field in the form instead.
                onClose: function (selectedDates, dateStr, instance) {
                    var focusable = Array.prototype.slice.call(
                        document.querySelectorAll('input, select, textarea, button, a[href]')
                    ).filter(function (node) {
                        return node.offsetParent !== null && !node.disabled && node.tabIndex !== -1;
                    });
                    var anchor = instance.altInput || instance.input;
                    var idx = focusable.indexOf(anchor);
                    if (idx > -1 && idx + 1 < focusable.length) {
                        focusable[idx + 1].focus();
                    }
                },
            };
            if (el.dataset.maxToday) opts.maxDate = 'today';
            if (!el.value) opts.defaultDate = 'today';

            flatpickr(el, opts);
        });
    };

    // Any <input data-uppercase> / <textarea data-uppercase> uppercases what
    // the user types live, instead of only on save - cursor position is
    // preserved so typing in the middle of a value doesn't jump to the end.
    window.enhanceUppercaseInputs = function () {
        document.querySelectorAll('[data-uppercase]').forEach(function (el) {
            if (el.dataset.ucEnhanced) return;
            el.dataset.ucEnhanced = '1';
            el.addEventListener('input', function () {
                var start = el.selectionStart, end = el.selectionEnd;
                el.value = el.value.toUpperCase();
                if (start !== null) el.setSelectionRange(start, end);
            });
        });
    };

    document.addEventListener('DOMContentLoaded', window.enhanceSearchableSelects);
    document.addEventListener('DOMContentLoaded', window.enhanceDropdownSearchSelects);
    document.addEventListener('DOMContentLoaded', window.enhanceDatepickers);
    document.addEventListener('DOMContentLoaded', window.enhanceUppercaseInputs);
})();
