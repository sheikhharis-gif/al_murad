(function () {
    'use strict';

    // Sidebar toggle (mobile)
    var toggle = document.getElementById('sidebarToggle');
    var sidebar = document.getElementById('sidebar');
    var overlay = document.getElementById('sidebarOverlay');

    if (toggle && sidebar) {
        toggle.addEventListener('click', function () {
            sidebar.classList.toggle('open');
            if (overlay) overlay.classList.toggle('show');
        });
    }

    if (overlay && sidebar) {
        overlay.addEventListener('click', function () {
            sidebar.classList.remove('open');
            overlay.classList.remove('show');
        });
    }

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
})();
