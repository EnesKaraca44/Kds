/* ============================================
   KDS - Main JavaScript
   ============================================ */

document.addEventListener('DOMContentLoaded', function () {

    // --------- Sidebar Toggle ---------
    const sidebar = document.getElementById('sidebar');
    const hamburger = document.getElementById('hamburgerBtn');
    const sidebarClose = document.getElementById('sidebarClose');

    if (hamburger) {
        hamburger.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    if (sidebarClose) {
        sidebarClose.addEventListener('click', () => {
            sidebar.classList.remove('open');
        });
    }

    // --------- Date Filter ---------
    const quickSelect = document.getElementById('quickSelect');
    const customDates = document.getElementById('customDates');

    if (quickSelect) {
        function toggleCustomDates() {
            if (quickSelect.value === 'ozel') {
                customDates.style.display = 'flex';
            } else {
                customDates.style.display = 'none';
            }
        }
        quickSelect.addEventListener('change', toggleCustomDates);
        toggleCustomDates(); // İlk yüklemede kontrol
    }

    // --------- Tabs ---------
    document.querySelectorAll('.tabs').forEach(tabContainer => {
        const buttons = tabContainer.querySelectorAll('.tab-btn');
        const contentSelector = tabContainer.dataset.target;
        const contents = document.querySelectorAll(contentSelector + ' .tab-content');

        buttons.forEach((btn, index) => {
            btn.addEventListener('click', () => {
                buttons.forEach(b => b.classList.remove('active'));
                contents.forEach(c => c.classList.remove('active'));

                btn.classList.add('active');
                if (contents[index]) {
                    contents[index].classList.add('active');

                    // Plotly grafikleri gizli tab'dan gösterilince yeniden boyutlandır
                    setTimeout(() => {
                        contents[index].querySelectorAll('.js-plotly-plot').forEach(plot => {
                            Plotly.Plots.resize(plot);
                        });
                    }, 50);
                }
            });
        });
    });

    // --------- Plotly Grafik Resize (responsive) ---------
    window.addEventListener('resize', function () {
        document.querySelectorAll('.js-plotly-plot').forEach(plot => {
            Plotly.Plots.resize(plot);
        });
    });

    // --------- Metric Card Entrance Animation ---------
    // CSS animasyonu ile otomatik çalışır, ekstra JS gerekmez.

    console.log('🏥 KDS Panel hazır.');
});
