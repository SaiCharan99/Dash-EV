"""
Unit tests for Energy Dashboard and EV Dashboard tab routing.

The render_tab callbacks return Dash component trees. We extract the registered
callback function via app.callback_map and call it directly — no browser needed.
"""

import pytest
from dash import html, dcc
import plotly.graph_objects as go


import json


def _call_tab_callback(app, tab_value):
    """
    Call the render_tab callback via Flask's test client.

    Dash wraps callbacks with context middleware (requires 'outputs_list').
    Calling through the HTTP interface bypasses that entirely.
    Flask routes are always at the root level regardless of requests_pathname_prefix.
    """
    client = app.server.test_client()
    payload = {
        'output': 'en-tab-content.children',
        'outputs': {'id': 'en-tab-content', 'property': 'children'},
        'inputs': [{'id': 'en-main-tabs', 'property': 'value', 'value': tab_value}],
        'changedPropIds': ['en-main-tabs.value'],
        'state': [],
    }
    resp = client.post(
        '/_dash-update-component',
        data=json.dumps(payload),
        content_type='application/json',
    )
    if resp.status_code != 200:
        return None
    data = json.loads(resp.data)
    return data.get('response', {}).get('en-tab-content', {}).get('children')


def _find_all(component, component_type, results=None):
    """Recursively find all components of a given type."""
    if results is None:
        results = []
    if isinstance(component, component_type):
        results.append(component)
    children = getattr(component, 'children', None)
    if isinstance(children, list):
        for child in children:
            _find_all(child, component_type, results)
    elif children is not None and hasattr(children, 'children'):
        _find_all(children, component_type, results)
    return results


# ── Energy Dashboard tab routing ─────────────────────────────────────────────

@pytest.fixture(scope='module')
def energy_app():
    from products.energy_dashboard.app import app
    return app


class TestEnergyTabRouting:
    """
    Tests render_tab via Flask test client (HTTP POST to /_dash-update-component).
    The response is a JSON tree — we check for graph IDs as strings in it.
    """
    TABS = ['demand', 'generation', 'economics', 'renewables', 'comparison']

    def _graph_ids_in_response(self, raw):
        """Flatten the JSON response tree and collect all 'id' values."""
        ids = set()
        if isinstance(raw, dict):
            if 'props' in raw and isinstance(raw['props'], dict):
                comp_id = raw['props'].get('id')
                if comp_id:
                    ids.add(comp_id)
            for v in raw.values():
                ids |= self._graph_ids_in_response(v)
        elif isinstance(raw, list):
            for item in raw:
                ids |= self._graph_ids_in_response(item)
        return ids

    def test_all_tabs_return_content(self, energy_app):
        for tab in self.TABS:
            result = _call_tab_callback(energy_app, tab)
            assert result is not None, f'Tab {tab!r} returned None from server'

    def test_demand_tab_contains_graph_ids(self, energy_app):
        result = _call_tab_callback(energy_app, 'demand')
        ids = self._graph_ids_in_response(result)
        for gid in ('dem-timeseries', 'dem-seasonal-box', 'dem-heatmap'):
            assert gid in ids, f'{gid!r} missing from demand tab'

    def test_generation_tab_contains_graph_ids(self, energy_app):
        result = _call_tab_callback(energy_app, 'generation')
        ids = self._graph_ids_in_response(result)
        for gid in ('gen-trend-lines', 'gen-donut', 'gen-stacked-bar', 'gen-monthly-area'):
            assert gid in ids, f'{gid!r} missing from generation tab'

    def test_economics_tab_contains_graph_ids(self, energy_app):
        result = _call_tab_callback(energy_app, 'economics')
        ids = self._graph_ids_in_response(result)
        for gid in ('econ-lcoe-range', 'econ-lcoe-trend', 'econ-price-vs-lcoe', 'econ-demand-cost'):
            assert gid in ids, f'{gid!r} missing from economics tab'

    def test_renewables_tab_contains_graph_ids(self, energy_app):
        result = _call_tab_callback(energy_app, 'renewables')
        ids = self._graph_ids_in_response(result)
        for gid in ('ren-share-bar', 'ren-cf-heatmap', 'ren-growth-waterfall'):
            assert gid in ids, f'{gid!r} missing from renewables tab'

    def test_comparison_tab_contains_graph_ids(self, energy_app):
        result = _call_tab_callback(energy_app, 'comparison')
        ids = self._graph_ids_in_response(result)
        for gid in ('sc-grouped-bar', 'sc-radar', 'sc-price-map'):
            assert gid in ids, f'{gid!r} missing from comparison tab'

    def test_unknown_tab_returns_no_update_or_none(self, energy_app):
        result = _call_tab_callback(energy_app, 'nonexistent')
        # unknown tab → None or a Dash no_update sentinel in the response
        assert result is None or result == {'_type': 'no_update'}


# ── Energy Dashboard static layout ───────────────────────────────────────────

class TestEnergyAppLayout:
    def test_layout_is_html_div(self, energy_app):
        assert isinstance(energy_app.layout, html.Div)

    def test_has_five_tabs(self, energy_app):
        tabs_comps = _find_all(energy_app.layout, dcc.Tabs)
        assert len(tabs_comps) == 1
        tab_list = tabs_comps[0].children
        assert len(tab_list) == 5

    def test_tab_values(self, energy_app):
        tabs_comps = _find_all(energy_app.layout, dcc.Tabs)
        values = [t.value for t in tabs_comps[0].children]
        assert set(values) == {'demand', 'generation', 'economics', 'renewables', 'comparison'}

    def test_default_tab_is_demand(self, energy_app):
        tabs_comps = _find_all(energy_app.layout, dcc.Tabs)
        assert tabs_comps[0].value == 'demand'

    def test_has_year_slider(self, energy_app):
        sliders = _find_all(energy_app.layout, dcc.RangeSlider)
        slider_ids = [s.id for s in sliders]
        assert 'en-yr-slider' in slider_ids

    def test_year_slider_range(self, energy_app):
        sliders = _find_all(energy_app.layout, dcc.RangeSlider)
        slider = next(s for s in sliders if s.id == 'en-yr-slider')
        assert slider.min == 2015
        assert slider.max == 2024

    def test_has_region_dropdown(self, energy_app):
        dropdowns = _find_all(energy_app.layout, dcc.Dropdown)
        ids = [d.id for d in dropdowns]
        assert 'en-region-filter' in ids

    def test_region_dropdown_options(self, energy_app):
        dropdowns = _find_all(energy_app.layout, dcc.Dropdown)
        dd = next(d for d in dropdowns if d.id == 'en-region-filter')
        option_vals = [o['value'] for o in dd.options]
        assert set(option_vals) == {'NSW', 'VIC', 'QLD', 'SA', 'TAS'}

    def test_region_dropdown_defaults_to_all(self, energy_app):
        dropdowns = _find_all(energy_app.layout, dcc.Dropdown)
        dd = next(d for d in dropdowns if d.id == 'en-region-filter')
        assert set(dd.value) == {'NSW', 'VIC', 'QLD', 'SA', 'TAS'}

    def test_has_season_filter(self, energy_app):
        radios = _find_all(energy_app.layout, dcc.RadioItems)
        ids = [r.id for r in radios]
        assert 'en-season-filter' in ids

    def test_season_filter_default_all(self, energy_app):
        radios = _find_all(energy_app.layout, dcc.RadioItems)
        radio = next(r for r in radios if r.id == 'en-season-filter')
        assert radio.value == 'All'

    def test_has_five_kpi_tiles(self, energy_app):
        divs = _find_all(energy_app.layout, html.Div)
        ids = [d.id for d in divs if hasattr(d, 'id')]
        for kpi_id in ('en-kpi-total', 'en-kpi-peak', 'en-kpi-renew', 'en-kpi-price', 'en-kpi-yoy'):
            assert kpi_id in ids, f'KPI tile {kpi_id!r} not found'

    def test_home_link_present(self, energy_app):
        links = _find_all(energy_app.layout, html.A)
        home_links = [l for l in links if getattr(l, 'href', '') == '/']
        assert len(home_links) >= 1

    def test_tab_content_placeholder_present(self, energy_app):
        divs = _find_all(energy_app.layout, html.Div)
        ids = [d.id for d in divs if hasattr(d, 'id')]
        assert 'en-tab-content' in ids


# ── EV Dashboard static layout ───────────────────────────────────────────────

@pytest.fixture(scope='module')
def ev_app():
    import os
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    csv = os.path.join(ROOT, 'data', 'ev_population.csv')
    if not os.path.exists(csv):
        pytest.skip('ev_population.csv not present')
    from products.ev_dashboard.app import app
    return app


class TestEvAppLayout:
    def test_layout_is_html_div(self, ev_app):
        assert isinstance(ev_app.layout, html.Div)

    def test_has_five_tabs(self, ev_app):
        tabs_comps = _find_all(ev_app.layout, dcc.Tabs)
        assert len(tabs_comps) == 1
        assert len(tabs_comps[0].children) == 5

    def test_tab_values(self, ev_app):
        tabs_comps = _find_all(ev_app.layout, dcc.Tabs)
        values = [t.value for t in tabs_comps[0].children]
        assert set(values) == {'overview', 'mfr', 'models', 'geo', 'global'}

    def test_default_tab_is_overview(self, ev_app):
        tabs_comps = _find_all(ev_app.layout, dcc.Tabs)
        assert tabs_comps[0].value == 'overview'

    def test_has_year_slider(self, ev_app):
        sliders = _find_all(ev_app.layout, dcc.RangeSlider)
        assert len(sliders) >= 1

    def test_has_ev_type_dropdown(self, ev_app):
        dropdowns = _find_all(ev_app.layout, dcc.Dropdown)
        ids = [d.id for d in dropdowns if hasattr(d, 'id')]
        # EV dashboard has a type and make dropdown
        assert len(ids) >= 1

    def test_home_link_present(self, ev_app):
        links = _find_all(ev_app.layout, html.A)
        home_links = [l for l in links if getattr(l, 'href', '') == '/']
        assert len(home_links) >= 1

    def test_has_h1_title(self, ev_app):
        h1s = _find_all(ev_app.layout, html.H1)
        assert len(h1s) == 1
        assert 'EV' in h1s[0].children or 'Market' in h1s[0].children
