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
    }

    window.enhanceSearchableSelects = function () {
        document.querySelectorAll('select.searchable-select').forEach(enhanceSearchableSelect);
    };

    document.addEventListener('DOMContentLoaded', window.enhanceSearchableSelects);
})();
