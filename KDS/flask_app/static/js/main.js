/* ============================================
   KDS - Main JavaScript
   ============================================ */

document.addEventListener('DOMContentLoaded', function () {
    const THEME_STORAGE_KEY = 'kds-theme';
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const themeLabel = document.getElementById('themeLabel');

    function applyPlotlyThemeToScope(theme, scope = document) {
        if (typeof Plotly === 'undefined') {
            return;
        }

        const isDark = theme === 'dark';
        const textColor = isDark ? '#e8f0fe' : '#0f172a';
        const mutedTextColor = isDark ? '#cbd5e1' : '#334155';
        const gridColor = isDark ? 'rgba(148, 163, 184, 0.25)' : 'rgba(100, 116, 139, 0.2)';
        const axisLineColor = isDark ? 'rgba(148, 163, 184, 0.45)' : 'rgba(71, 85, 105, 0.45)';
        const plotBgColor = isDark ? '#0b1a3a' : '#ffffff';
        const paperBgColor = isDark ? '#0b1a3a' : '#ffffff';
        const modebarBg = isDark ? 'rgba(15, 23, 42, 0.7)' : 'rgba(241, 245, 249, 0.9)';

        scope.querySelectorAll('.js-plotly-plot, .plotly-graph-div').forEach(plot => {
            if (!plot || !plot.layout) {
                return;
            }

            const relayoutConfig = {
                'paper_bgcolor': paperBgColor,
                'plot_bgcolor': plotBgColor,
                'font.color': textColor,
                'title.font.color': textColor,
                'legend.font.color': textColor,
                'xaxis.color': mutedTextColor,
                'xaxis.tickfont.color': mutedTextColor,
                'xaxis.title.font.color': textColor,
                'xaxis.gridcolor': gridColor,
                'xaxis.zerolinecolor': gridColor,
                'xaxis.linecolor': axisLineColor,
                'yaxis.color': mutedTextColor,
                'yaxis.tickfont.color': mutedTextColor,
                'yaxis.title.font.color': textColor,
                'yaxis.gridcolor': gridColor,
                'yaxis.zerolinecolor': gridColor,
                'yaxis.linecolor': axisLineColor,
                'coloraxis.colorbar.tickfont.color': mutedTextColor,
                'coloraxis.colorbar.title.font.color': textColor
            };

            Object.keys(plot.layout || {}).forEach(key => {
                if (/^(xaxis|yaxis)\d+$/.test(key)) {
                    relayoutConfig[`${key}.color`] = mutedTextColor;
                    relayoutConfig[`${key}.tickfont.color`] = mutedTextColor;
                    relayoutConfig[`${key}.title.font.color`] = textColor;
                    relayoutConfig[`${key}.gridcolor`] = gridColor;
                    relayoutConfig[`${key}.zerolinecolor`] = gridColor;
                    relayoutConfig[`${key}.linecolor`] = axisLineColor;
                }
            });

            try {
                const result = Plotly.relayout(plot, relayoutConfig);
                if (result && typeof result.catch === 'function') {
                    result.catch(() => {
                        // Some plot types may not support all relayout keys; ignore safely.
                    });
                }
            } catch (_) {
                // Ignore theme relayout failures on partially initialized charts.
            }

            const modebar = plot.parentElement?.querySelector('.modebar');
            if (modebar) {
                modebar.style.background = modebarBg;
            }
        });
    }

    function refreshPlotsInScope(scope = document) {
        if (typeof Plotly === 'undefined') {
            return;
        }

        const activeTheme = document.body.classList.contains('theme-dark') ? 'dark' : 'light';
        [80, 220, 500].forEach(delay => {
            setTimeout(() => {
                scope.querySelectorAll('.js-plotly-plot, .plotly-graph-div').forEach(plot => {
                    if (!plot) {
                        return;
                    }

                    try {
                        Plotly.Plots.resize(plot);
                        Plotly.redraw(plot);
                    } catch (_) {
                        // Ignore charts that are not ready yet; the next delayed pass retries.
                    }
                });
                applyPlotlyThemeToScope(activeTheme, scope);
            }, delay);
        });
    }

    function getInitialTheme() {
        const storedTheme = localStorage.getItem(THEME_STORAGE_KEY);
        if (storedTheme === 'dark' || storedTheme === 'light') {
            return storedTheme;
        }
        return document.body.classList.contains('theme-dark') ? 'dark' : 'light';
    }

    function applyTheme(theme) {
        const normalizedTheme = theme === 'dark' ? 'dark' : 'light';
        document.body.classList.remove('theme-dark', 'theme-light');
        document.body.classList.add(`theme-${normalizedTheme}`);
        document.documentElement.setAttribute('data-theme', normalizedTheme);

        if (themeToggle) {
            themeToggle.setAttribute('aria-pressed', normalizedTheme === 'dark' ? 'true' : 'false');
        }
        if (themeIcon) {
            themeIcon.textContent = normalizedTheme === 'dark' ? '☀️' : '🌙';
        }
        if (themeLabel) {
            themeLabel.textContent = normalizedTheme === 'dark' ? 'Aydinlik' : 'Koyu';
        }
        refreshPlotsInScope(document);
    }

    applyTheme(getInitialTheme());

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = document.body.classList.contains('theme-dark') ? 'dark' : 'light';
            const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(nextTheme);
            localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
        });
    }

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

                    // Hidden tabs need a couple of delayed resizes before Plotly settles.
                    refreshPlotsInScope(contents[index]);
                }
            });
        });
    });

    // --------- Plotly Grafik Resize (responsive) ---------
    window.addEventListener('resize', function () {
        refreshPlotsInScope(document);
    });

    // --------- Metric Card Entrance Animation ---------
    // CSS animasyonu ile otomatik çalışır, ekstra JS gerekmez.

    console.log('🏥 KDS Panel hazır.');
});
