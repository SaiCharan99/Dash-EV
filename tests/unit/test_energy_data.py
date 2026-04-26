"""
Unit tests for products/energy_dashboard/data.py filter functions.
All tests use the patched_cache fixture (in-memory DataFrames, no disk I/O).
"""

import pytest
import pandas as pd


class TestFilterDemand:
    def test_returns_dataframe(self, patched_cache):
        from products.energy_dashboard.data import filter_demand
        df = filter_demand()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    def test_year_range_filter(self, patched_cache):
        from products.energy_dashboard.data import filter_demand
        df = filter_demand(yr_range=(2020, 2022))
        assert df['year'].min() >= 2020
        assert df['year'].max() <= 2022

    def test_region_filter_single(self, patched_cache):
        from products.energy_dashboard.data import filter_demand
        df = filter_demand(regions=['NSW'])
        assert set(df['region'].unique()) == {'NSW'}

    def test_region_filter_multiple(self, patched_cache):
        from products.energy_dashboard.data import filter_demand
        df = filter_demand(regions=['NSW', 'VIC'])
        assert set(df['region'].unique()).issubset({'NSW', 'VIC'})

    def test_season_filter(self, patched_cache):
        from products.energy_dashboard.data import filter_demand
        df = filter_demand(season='summer')
        assert (df['season'] == 'summer').all()

    def test_season_all_returns_all(self, patched_cache):
        from products.energy_dashboard.data import filter_demand
        df_all    = filter_demand(season='All')
        df_no_sea = filter_demand(season=None)
        assert len(df_all) == len(df_no_sea)

    def test_returns_none_when_cache_empty(self, monkeypatch):
        import api.cache as cache
        monkeypatch.setattr(cache, '_demand_df', None)
        from products.energy_dashboard.data import filter_demand
        assert filter_demand() is None

    def test_combined_filters(self, patched_cache):
        from products.energy_dashboard.data import filter_demand
        df = filter_demand(regions=['SA'], yr_range=(2018, 2020), season='winter')
        assert set(df['region'].unique()) == {'SA'}
        assert df['year'].between(2018, 2020).all()
        assert (df['season'] == 'winter').all()


class TestFilterGeneration:
    def test_returns_dataframe(self, patched_cache):
        from products.energy_dashboard.data import filter_generation
        df = filter_generation()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    def test_source_filter(self, patched_cache):
        from products.energy_dashboard.data import filter_generation
        df = filter_generation(sources=['solar_utility'])
        assert (df['source'] == 'solar_utility').all()

    def test_multiple_sources(self, patched_cache):
        from products.energy_dashboard.data import filter_generation
        df = filter_generation(sources=['solar_utility', 'wind'])
        assert set(df['source'].unique()).issubset({'solar_utility', 'wind'})

    def test_returns_none_when_cache_empty(self, monkeypatch):
        import api.cache as cache
        monkeypatch.setattr(cache, '_generation_df', None)
        from products.energy_dashboard.data import filter_generation
        assert filter_generation() is None

    def test_source_category_present(self, patched_cache):
        from products.energy_dashboard.data import filter_generation
        df = filter_generation()
        assert 'source_category' in df.columns

    def test_renewable_category_filter(self, patched_cache):
        from products.energy_dashboard.data import filter_generation
        df = filter_generation()
        ren = df[df['source_category'] == 'renewable']
        assert not ren.empty


class TestFilterPrices:
    def test_returns_dataframe(self, patched_cache):
        from products.energy_dashboard.data import filter_prices
        df = filter_prices()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    def test_region_filter(self, patched_cache):
        from products.energy_dashboard.data import filter_prices
        df = filter_prices(regions=['QLD'])
        assert set(df['region'].unique()) == {'QLD'}

    def test_year_range_filter(self, patched_cache):
        from products.energy_dashboard.data import filter_prices
        df = filter_prices(yr_range=(2022, 2024))
        assert df['year'].min() >= 2022
        assert df['year'].max() <= 2024

    def test_returns_none_when_cache_empty(self, monkeypatch):
        import api.cache as cache
        monkeypatch.setattr(cache, '_prices_df', None)
        from products.energy_dashboard.data import filter_prices
        assert filter_prices() is None

    def test_avg_spot_mwh_present(self, patched_cache):
        from products.energy_dashboard.data import filter_prices
        df = filter_prices()
        assert 'avg_spot_mwh' in df.columns
