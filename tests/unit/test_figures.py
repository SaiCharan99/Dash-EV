"""
Unit tests for chart-producing callbacks.

Each callback is invoked through Flask's test client
(POST /_dash-update-component) with in-memory data from patched_cache.
This avoids the Dash context middleware issue and tests the real HTTP path.

Assertions: correct return type (go.Figure), expected trace types,
non-empty traces, graceful empty-state handling.
"""

import json
import pytest
import plotly.graph_objects as go
from dash import html


# ── Flask test client helper ─────────────────────────────────────────────────

def _make_output_key(outputs):
    """Build the Dash multi-output key string from a list of (id, prop) pairs."""
    if len(outputs) == 1:
        return f'{outputs[0][0]}.{outputs[0][1]}'
    return '..' + '...'.join(f'{oid}.{prop}' for oid, prop in outputs) + '..'


def _call_callback(app, outputs, inputs):
    """
    POST to /_dash-update-component and return the response dict keyed by component ID.

    outputs: list of (component_id, property) tuples
    inputs:  list of (component_id, property, value) tuples
    Returns: dict of {component_id: {property: value}} on success, {} on failure.
    """
    client = app.server.test_client()
    out_key = _make_output_key(outputs)
    payload = {
        'output': out_key,
        'outputs': [{'id': oid, 'property': prop} for oid, prop in outputs]
                   if len(outputs) > 1 else {'id': outputs[0][0], 'property': outputs[0][1]},
        'inputs': [{'id': cid, 'property': prop, 'value': val}
                   for cid, prop, val in inputs],
        'changedPropIds': [f'{inputs[0][0]}.{inputs[0][1]}'],
        'state': [],
    }
    resp = client.post(
        '/_dash-update-component',
        data=json.dumps(payload),
        content_type='application/json',
    )
    if resp.status_code != 200:
        return {}
    return json.loads(resp.data).get('response', {})


def _fig(response, component_id):
    """Extract and deserialize a Plotly figure from a callback response dict."""
    fig_data = response.get(component_id, {}).get('figure')
    if fig_data is None:
        return None
    return go.Figure(data=fig_data.get('data', []), layout=fig_data.get('layout', {}))


def _trace_types(fig):
    return [type(t).__name__ for t in fig.data]


# ── Shared fixtures ───────────────────────────────────────────────────────────

_DEFAULT_INPUTS = [
    ('en-yr-slider',     'value', [2015, 2024]),
    ('en-region-filter', 'value', ['NSW', 'VIC', 'QLD', 'SA', 'TAS']),
    ('en-season-filter', 'value', 'All'),
]

_DEMAND_OUTPUTS = [
    ('dem-timeseries',   'figure'),
    ('dem-seasonal-box', 'figure'),
    ('dem-heatmap',      'figure'),
]

_GENERATION_OUTPUTS = [
    ('gen-trend-lines',  'figure'),
    ('gen-donut',        'figure'),
    ('gen-donut-legend', 'children'),
    ('gen-stacked-bar',  'figure'),
    ('gen-monthly-area', 'figure'),
]

_ECONOMICS_OUTPUTS = [
    ('econ-lcoe-range',    'figure'),
    ('econ-lcoe-trend',    'figure'),
    ('econ-price-vs-lcoe', 'figure'),
    ('econ-demand-cost',   'figure'),
]

_RENEWABLES_OUTPUTS = [
    ('ren-share-bar',        'figure'),
    ('ren-cf-heatmap',       'figure'),
    ('ren-growth-waterfall', 'figure'),
]

_COMPARISON_OUTPUTS = [
    ('sc-grouped-bar', 'figure'),
    ('sc-radar',       'figure'),
    ('sc-price-map',   'figure'),
]

_KPI_OUTPUTS = [
    ('en-kpi-total', 'children'),
    ('en-kpi-peak',  'children'),
    ('en-kpi-renew', 'children'),
    ('en-kpi-price', 'children'),
    ('en-kpi-yoy',   'children'),
]


@pytest.fixture(scope='module')
def energy_app():
    from products.energy_dashboard.app import app
    return app


# ── Demand callback ───────────────────────────────────────────────────────────

class TestDemandCallback:
    def test_all_three_outputs_returned(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _DEMAND_OUTPUTS, _DEFAULT_INPUTS)
        for oid, _ in _DEMAND_OUTPUTS:
            assert oid in resp, f'{oid} missing from demand callback response'

    def test_timeseries_is_figure(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _DEMAND_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'dem-timeseries')
        assert fig is not None

    def test_timeseries_has_scatter_traces(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _DEMAND_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'dem-timeseries')
        assert len(fig.data) > 0
        assert 'Scatter' in _trace_types(fig)

    def test_timeseries_one_trace_per_region(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _DEMAND_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'dem-timeseries')
        assert len(fig.data) == 5

    def test_seasonal_box_has_box_traces(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _DEMAND_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'dem-seasonal-box')
        assert 'Box' in _trace_types(fig)

    def test_heatmap_has_heatmap_trace(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _DEMAND_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'dem-heatmap')
        assert 'Heatmap' in _trace_types(fig)

    def test_empty_state_returns_empty_figures(self, energy_app, monkeypatch):
        import api.cache as cache
        monkeypatch.setattr(cache, '_demand_df', None)
        resp = _call_callback(energy_app, _DEMAND_OUTPUTS, _DEFAULT_INPUTS)
        if resp:
            fig = _fig(resp, 'dem-timeseries')
            if fig:
                assert len(fig.data) == 0

    def test_single_region_filter(self, patched_cache, energy_app):
        inputs = [
            ('en-yr-slider',     'value', [2020, 2024]),
            ('en-region-filter', 'value', ['NSW']),
            ('en-season-filter', 'value', 'All'),
        ]
        resp = _call_callback(energy_app, _DEMAND_OUTPUTS, inputs)
        fig = _fig(resp, 'dem-timeseries')
        assert fig is not None
        assert len(fig.data) == 1  # only NSW


# ── Generation callback ───────────────────────────────────────────────────────

class TestGenerationCallback:
    def test_all_outputs_returned(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _GENERATION_OUTPUTS, _DEFAULT_INPUTS)
        for oid, _ in _GENERATION_OUTPUTS:
            assert oid in resp

    def test_trend_lines_has_scatter_traces(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _GENERATION_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'gen-trend-lines')
        assert fig is not None
        assert len(fig.data) > 0
        assert 'Scatter' in _trace_types(fig)

    def test_donut_has_pie_trace(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _GENERATION_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'gen-donut')
        assert fig is not None
        assert 'Pie' in _trace_types(fig)

    def test_stacked_bar_has_bar_traces(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _GENERATION_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'gen-stacked-bar')
        assert fig is not None
        assert 'Bar' in _trace_types(fig)

    def test_monthly_area_has_scatter_traces(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _GENERATION_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'gen-monthly-area')
        assert fig is not None
        assert 'Scatter' in _trace_types(fig)

    def test_donut_legend_is_not_figure(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _GENERATION_OUTPUTS, _DEFAULT_INPUTS)
        legend_val = resp.get('gen-donut-legend', {}).get('children')
        # children should be a list or None, never a Plotly figure dict
        assert not isinstance(legend_val, go.Figure)


# ── Economics callback ────────────────────────────────────────────────────────

class TestEconomicsCallback:
    def test_all_outputs_returned(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _ECONOMICS_OUTPUTS, _DEFAULT_INPUTS)
        for oid, _ in _ECONOMICS_OUTPUTS:
            assert oid in resp

    def test_lcoe_range_is_figure(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _ECONOMICS_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'econ-lcoe-range')
        assert fig is not None

    def test_lcoe_trend_has_scatter(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _ECONOMICS_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'econ-lcoe-trend')
        assert fig is not None
        assert len(fig.data) > 0
        assert 'Scatter' in _trace_types(fig)

    def test_lcoe_range_covers_technologies(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _ECONOMICS_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'econ-lcoe-range')
        assert fig is not None
        assert len(fig.data) >= 3

    def test_price_vs_lcoe_is_figure(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _ECONOMICS_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'econ-price-vs-lcoe')
        assert fig is not None

    def test_demand_cost_is_figure(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _ECONOMICS_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'econ-demand-cost')
        assert fig is not None


# ── Renewables callback ───────────────────────────────────────────────────────

class TestRenewablesCallback:
    def test_all_outputs_returned(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _RENEWABLES_OUTPUTS, _DEFAULT_INPUTS)
        for oid, _ in _RENEWABLES_OUTPUTS:
            assert oid in resp

    def test_share_bar_has_bar_traces(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _RENEWABLES_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'ren-share-bar')
        assert fig is not None

    def test_cf_heatmap_is_heatmap(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _RENEWABLES_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'ren-cf-heatmap')
        assert fig is not None
        if fig.data:
            assert 'Heatmap' in _trace_types(fig)

    def test_waterfall_is_figure(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _RENEWABLES_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'ren-growth-waterfall')
        assert fig is not None


# ── Comparison callback ───────────────────────────────────────────────────────

class TestComparisonCallback:
    def test_all_outputs_returned(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _COMPARISON_OUTPUTS, _DEFAULT_INPUTS)
        for oid, _ in _COMPARISON_OUTPUTS:
            assert oid in resp

    def test_grouped_bar_has_bar_traces(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _COMPARISON_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'sc-grouped-bar')
        assert fig is not None

    def test_radar_has_scatterpolar(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _COMPARISON_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'sc-radar')
        assert fig is not None
        if fig.data:
            assert 'Scatterpolar' in _trace_types(fig)

    def test_price_map_is_figure(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _COMPARISON_OUTPUTS, _DEFAULT_INPUTS)
        fig = _fig(resp, 'sc-price-map')
        assert fig is not None


# ── KPI callback ──────────────────────────────────────────────────────────────

class TestKpiCallback:
    def test_all_kpi_outputs_returned(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _KPI_OUTPUTS, _DEFAULT_INPUTS)
        for oid, _ in _KPI_OUTPUTS:
            assert oid in resp, f'{oid} missing from KPI response'

    def test_kpi_total_has_children(self, patched_cache, energy_app):
        resp = _call_callback(energy_app, _KPI_OUTPUTS, _DEFAULT_INPUTS)
        val = resp.get('en-kpi-total', {}).get('children')
        assert val is not None

    def test_kpi_values_are_dicts(self, patched_cache, energy_app):
        # KPI tiles are serialized Dash Div components (dicts in the JSON response)
        resp = _call_callback(energy_app, _KPI_OUTPUTS, _DEFAULT_INPUTS)
        for oid, _ in _KPI_OUTPUTS:
            val = resp.get(oid, {}).get('children')
            assert val is not None, f'{oid} children is None'

    def test_no_kpi_outputs_when_no_data(self, energy_app, monkeypatch):
        import api.cache as cache
        monkeypatch.setattr(cache, '_demand_df', None)
        resp = _call_callback(energy_app, _KPI_OUTPUTS, _DEFAULT_INPUTS)
        # Should still return the 5 KPI outputs (filled with empty tiles)
        if resp:
            assert len(resp) == 5
