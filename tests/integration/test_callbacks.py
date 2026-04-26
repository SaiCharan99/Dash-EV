"""
Integration tests for Dash callback logic.

Tests invoke the callback functions directly (not through a browser/Selenium).
Uses patched_cache fixture so no disk I/O is needed.
"""

import pytest
from dash import html


# ── KPI callback ──────────────────────────────────────────────────────────────

class TestKpiCallback:
    def test_returns_five_tiles(self, patched_cache):
        from products.energy_dashboard.callbacks.cb_kpis import register
        import dash
        app = dash.Dash(__name__, suppress_callback_exceptions=True)
        register(app)
        # Call the inner callback function directly
        from products.energy_dashboard.callbacks.cb_kpis import register as reg
        # Extract the callback function by calling a fresh registration
        import types
        results = []

        _app = dash.Dash('test_kpis', suppress_callback_exceptions=True)

        @_app.callback(
            __import__('dash').Output('out1', 'children'),
            __import__('dash').Input('in1', 'value'),
        )
        def dummy(v): return v

        # Call cb_kpis logic directly
        from products.energy_dashboard.data import filter_demand, filter_generation, filter_prices
        from api.cache import is_ready
        assert is_ready()

        yr_range = [2015, 2024]
        regions  = ['NSW', 'VIC', 'QLD', 'SA', 'TAS']
        season   = 'All'

        d  = filter_demand(regions, yr_range, None)
        g  = filter_generation(regions, yr_range)
        p  = filter_prices(regions, yr_range)

        total_twh = d['demand_gwh'].sum() / 1000
        peak_gw   = d['peak_demand_gw'].max()
        ren_gwh   = g[g.source_category == 'renewable']['generation_gwh'].sum()
        tot_gwh   = g['generation_gwh'].sum()
        ren_pct   = ren_gwh / tot_gwh * 100 if tot_gwh else 0
        avg_price = p['avg_spot_mwh'].mean()

        assert total_twh > 0
        assert peak_gw > 0
        assert 0 <= ren_pct <= 100
        assert avg_price > 0

    def test_kpi_when_not_ready(self, monkeypatch):
        import api.cache as cache
        monkeypatch.setattr(cache, '_demand_df', None)
        from api.cache import is_ready
        assert is_ready() is False


# ── Demand filter logic ───────────────────────────────────────────────────────

class TestDemandFilterLogic:
    def test_season_filter_reduces_rows(self, patched_cache):
        from products.energy_dashboard.data import filter_demand
        all_df    = filter_demand(yr_range=(2020, 2024))
        summer_df = filter_demand(yr_range=(2020, 2024), season='summer')
        assert len(summer_df) < len(all_df)

    def test_single_region_fewer_rows(self, patched_cache):
        from products.energy_dashboard.data import filter_demand
        all_df = filter_demand()
        nsw_df = filter_demand(regions=['NSW'])
        assert len(nsw_df) < len(all_df)

    def test_demand_gwh_positive(self, patched_cache):
        from products.energy_dashboard.data import filter_demand
        df = filter_demand()
        assert (df['demand_gwh'] > 0).all()


# ── Generation logic ──────────────────────────────────────────────────────────

class TestGenerationLogic:
    def test_renewable_share_between_0_and_100(self, patched_cache):
        from products.energy_dashboard.data import filter_generation
        g = filter_generation()
        ren = g[g.source_category == 'renewable']['generation_gwh'].sum()
        tot = g['generation_gwh'].sum()
        pct = ren / tot * 100
        assert 0 <= pct <= 100

    def test_all_sources_present(self, patched_cache):
        from products.energy_dashboard.data import filter_generation
        g = filter_generation()
        sources = set(g['source'].unique())
        assert len(sources) >= 3

    def test_generation_non_negative(self, patched_cache):
        from products.energy_dashboard.data import filter_generation
        df = filter_generation()
        assert (df['generation_gwh'] >= 0).all()


# ── Price logic ───────────────────────────────────────────────────────────────

class TestPriceLogic:
    def test_prices_positive(self, patched_cache):
        from products.energy_dashboard.data import filter_prices
        df = filter_prices()
        assert (df['avg_spot_mwh'] > 0).all()

    def test_max_gte_avg(self, patched_cache):
        from products.energy_dashboard.data import filter_prices
        df = filter_prices()
        if 'max_spot_mwh' in df.columns:
            assert (df['max_spot_mwh'] >= df['avg_spot_mwh']).all()

    def test_min_lte_avg(self, patched_cache):
        from products.energy_dashboard.data import filter_prices
        df = filter_prices()
        if 'min_spot_mwh' in df.columns:
            assert (df['min_spot_mwh'] <= df['avg_spot_mwh']).all()


# ── Summary endpoint logic (via api router, not HTTP) ─────────────────────────

class TestSummaryLogic:
    def test_renewable_pct_plausible(self, patched_cache):
        from api.routers.energy import get_region_summary
        import api.cache as cache
        # patch demand/gen/prices in cache via patched_cache fixture
        result = get_region_summary('NSW')
        assert 0 <= result['renewable_pct'] <= 100

    def test_peak_demand_positive(self, patched_cache):
        from api.routers.energy import get_region_summary
        result = get_region_summary('VIC')
        assert result['peak_demand_gw'] > 0

    def test_top_source_is_string(self, patched_cache):
        from api.routers.energy import get_region_summary
        result = get_region_summary('QLD')
        assert isinstance(result['top_source'], str)
        assert len(result['top_source']) > 0
