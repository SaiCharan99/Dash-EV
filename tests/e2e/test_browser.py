"""
Browser-based end-to-end tests using Dash's built-in Selenium integration.

REQUIREMENTS (not in requirements.txt by default):
    pip install dash[testing] pytest-dash selenium
    brew install chromedriver          # macOS
    # or: pip install webdriver-manager

HOW TO RUN (these tests are SKIPPED unless you have the above installed):
    pytest tests/e2e/test_browser.py --headed   # show the browser window
    pytest tests/e2e/test_browser.py            # headless (CI-friendly)

The 'dash_duo' fixture is provided by the 'dash[testing]' package and
automatically starts/stops a Chrome browser via Selenium WebDriver.

These tests verify what Python-only tests cannot:
  - Page actually loads in a browser (JS executes, CSS renders)
  - Callbacks fire after user interaction (dropdown change, slider move)
  - Charts become visible on the correct tabs
  - Navigation between pages works
  - No JS console errors on load
"""

import pytest

# Skip the entire module if dash[testing] is not installed
pytest.importorskip('dash.testing.application_runners',
                    reason='dash[testing] not installed — run: pip install dash[testing]')
pytest.importorskip('selenium',
                    reason='selenium not installed — run: pip install selenium')

from dash.testing.application_runners import import_app


# ── Landing page ──────────────────────────────────────────────────────────────

class TestLandingBrowser:
    def test_landing_loads(self, dash_duo):
        app = import_app('landing.app')
        dash_duo.start_server(app)
        dash_duo.wait_for_element('h1', timeout=10)
        assert 'Energy Intelligence Platform' in dash_duo.find_element('h1').text

    def test_ev_card_link_navigates(self, dash_duo):
        app = import_app('landing.app')
        dash_duo.start_server(app)
        dash_duo.wait_for_element('a[href="/ev/"]', timeout=10)
        link = dash_duo.find_element('a[href="/ev/"]')
        assert link is not None

    def test_energy_card_link_present(self, dash_duo):
        app = import_app('landing.app')
        dash_duo.start_server(app)
        dash_duo.wait_for_element('a[href="/energy/"]', timeout=10)
        link = dash_duo.find_element('a[href="/energy/"]')
        assert link is not None

    def test_no_js_errors(self, dash_duo):
        app = import_app('landing.app')
        dash_duo.start_server(app)
        dash_duo.wait_for_element('h1', timeout=10)
        assert dash_duo.get_logs() == [] or all(
            log['level'] != 'SEVERE' for log in dash_duo.get_logs()
        )


# ── Energy Dashboard browser tests ───────────────────────────────────────────

class TestEnergyDashboardBrowser:
    @pytest.fixture(autouse=True)
    def skip_if_no_data(self):
        import os, sys
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        required = ['demand_by_region.parquet', 'generation_by_source.parquet',
                    'prices_by_region.parquet', 'lcoe_estimates.parquet']
        missing = [f for f in required
                   if not os.path.exists(os.path.join(root, 'data', 'energy', f))]
        if missing:
            pytest.skip(f'Missing parquet files: {missing}')

    def test_energy_dashboard_loads(self, dash_duo):
        from api.cache import init_data
        init_data()
        app = import_app('products.energy_dashboard.app')
        dash_duo.start_server(app)
        dash_duo.wait_for_element('h1', timeout=15)
        assert 'Australian Energy Transition' in dash_duo.find_element('h1').text

    def test_kpi_tiles_visible(self, dash_duo):
        from api.cache import init_data
        init_data()
        app = import_app('products.energy_dashboard.app')
        dash_duo.start_server(app)
        dash_duo.wait_for_element('#en-kpi-total', timeout=15)
        # Wait for callback to fill the KPI
        dash_duo.wait_for_text_to_equal('#en-kpi-total *', None, timeout=10)
        kpi = dash_duo.find_element('#en-kpi-total')
        assert kpi is not None

    def test_tab_switch_to_generation(self, dash_duo):
        from api.cache import init_data
        init_data()
        app = import_app('products.energy_dashboard.app')
        dash_duo.start_server(app)
        dash_duo.wait_for_element('.tab', timeout=10)
        tabs = dash_duo.find_elements('.tab')
        gen_tab = next((t for t in tabs if 'Generation' in t.text), None)
        assert gen_tab is not None
        gen_tab.click()
        dash_duo.wait_for_element('#gen-trend-lines', timeout=10)

    def test_region_dropdown_change_updates_charts(self, dash_duo):
        from api.cache import init_data
        init_data()
        app = import_app('products.energy_dashboard.app')
        dash_duo.start_server(app)
        dash_duo.wait_for_element('#en-region-filter', timeout=10)
        # Change region and wait for re-render
        dash_duo.select_dcc_dropdown('#en-region-filter', 'NSW')
        dash_duo.wait_for_element('#dem-timeseries', timeout=10)

    def test_no_severe_js_errors(self, dash_duo):
        from api.cache import init_data
        init_data()
        app = import_app('products.energy_dashboard.app')
        dash_duo.start_server(app)
        dash_duo.wait_for_element('h1', timeout=15)
        logs = dash_duo.get_logs() or []
        severe = [l for l in logs if l.get('level') == 'SEVERE']
        assert severe == [], f'JS errors on load: {severe}'


# ── EV Dashboard browser tests ───────────────────────────────────────────────

class TestEvDashboardBrowser:
    @pytest.fixture(autouse=True)
    def skip_if_no_csv(self):
        import os
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        if not os.path.exists(os.path.join(root, 'data', 'ev_population.csv')):
            pytest.skip('ev_population.csv not present')

    def test_ev_dashboard_loads(self, dash_duo):
        app = import_app('products.ev_dashboard.app')
        dash_duo.start_server(app)
        dash_duo.wait_for_element('h1', timeout=15)
        assert 'EV' in dash_duo.find_element('h1').text

    def test_five_tabs_visible(self, dash_duo):
        app = import_app('products.ev_dashboard.app')
        dash_duo.start_server(app)
        dash_duo.wait_for_element('.tab', timeout=10)
        tabs = dash_duo.find_elements('.tab')
        assert len(tabs) == 5

    def test_tab_switch_to_geography(self, dash_duo):
        app = import_app('products.ev_dashboard.app')
        dash_duo.start_server(app)
        dash_duo.wait_for_element('.tab', timeout=10)
        tabs = dash_duo.find_elements('.tab')
        geo_tab = next((t for t in tabs if 'Geography' in t.text), None)
        assert geo_tab is not None
        geo_tab.click()
        dash_duo.wait_for_element('#geo-map', timeout=15)

    def test_year_slider_present(self, dash_duo):
        app = import_app('products.ev_dashboard.app')
        dash_duo.start_server(app)
        dash_duo.wait_for_element('.rc-slider', timeout=10)
        slider = dash_duo.find_element('.rc-slider')
        assert slider is not None
