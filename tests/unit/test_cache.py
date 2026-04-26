"""
Unit tests for api/cache.py — accessor functions and init_data().
Uses monkeypatching (patched_cache fixture) to avoid disk reads.
"""

import pytest
import pandas as pd


class TestCacheAccessors:
    def test_is_ready_false_when_not_loaded(self):
        import api.cache as cache
        orig = cache._demand_df
        cache._demand_df = None
        from api.cache import is_ready
        assert is_ready() is False
        cache._demand_df = orig

    def test_is_ready_true_when_loaded(self, patched_cache):
        from api.cache import is_ready
        assert is_ready() is True

    def test_get_demand_df_returns_dataframe(self, patched_cache):
        from api.cache import get_demand_df
        df = get_demand_df()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    def test_get_generation_df_returns_dataframe(self, patched_cache):
        from api.cache import get_generation_df
        df = get_generation_df()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    def test_get_prices_df_returns_dataframe(self, patched_cache):
        from api.cache import get_prices_df
        df = get_prices_df()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    def test_get_lcoe_df_returns_dataframe(self, patched_cache):
        from api.cache import get_lcoe_df
        df = get_lcoe_df()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty


class TestDemandSchema:
    def test_required_columns(self, patched_cache):
        from api.cache import get_demand_df
        df = get_demand_df()
        for col in ('region', 'year', 'month', 'season', 'demand_gwh'):
            assert col in df.columns, f'Missing column: {col}'

    def test_regions_are_valid(self, patched_cache):
        from api.cache import get_demand_df
        valid = {'NSW', 'VIC', 'QLD', 'SA', 'TAS'}
        assert set(get_demand_df()['region'].unique()).issubset(valid)

    def test_years_in_range(self, patched_cache):
        from api.cache import get_demand_df
        df = get_demand_df()
        assert df['year'].min() >= 2015


class TestGenerationSchema:
    def test_required_columns(self, patched_cache):
        from api.cache import get_generation_df
        df = get_generation_df()
        for col in ('region', 'year', 'month', 'source', 'source_category', 'generation_gwh'):
            assert col in df.columns, f'Missing column: {col}'

    def test_source_category_values(self, patched_cache):
        from api.cache import get_generation_df
        valid = {'fossil', 'renewable', 'storage'}
        cats = set(get_generation_df()['source_category'].unique())
        assert cats.issubset(valid)


class TestPricesSchema:
    def test_required_columns(self, patched_cache):
        from api.cache import get_prices_df
        df = get_prices_df()
        for col in ('region', 'year', 'month', 'avg_spot_mwh'):
            assert col in df.columns, f'Missing column: {col}'

    def test_prices_non_negative(self, patched_cache):
        from api.cache import get_prices_df
        df = get_prices_df()
        assert (df['avg_spot_mwh'] >= 0).all()


class TestLcoeSchema:
    def test_required_columns(self, patched_cache):
        from api.cache import get_lcoe_df
        df = get_lcoe_df()
        for col in ('technology', 'year', 'lcoe_low', 'lcoe_mid', 'lcoe_high', 'is_projection'):
            assert col in df.columns, f'Missing column: {col}'

    def test_lcoe_ordering(self, patched_cache):
        from api.cache import get_lcoe_df
        df = get_lcoe_df()
        assert (df['lcoe_low'] <= df['lcoe_mid']).all()
        assert (df['lcoe_mid'] <= df['lcoe_high']).all()

    def test_projections_are_post_2024(self, patched_cache):
        from api.cache import get_lcoe_df
        df = get_lcoe_df()
        proj = df[df['is_projection'] == True]
        hist = df[df['is_projection'] == False]
        if not proj.empty:
            assert proj['year'].min() >= 2025
        if not hist.empty:
            assert hist['year'].max() <= 2024


class TestInitDataSkipsOnMissingFiles:
    def test_init_data_raises_without_files(self, tmp_path, monkeypatch):
        import api.cache as cache
        monkeypatch.setattr(cache, '_DATA_DIR', str(tmp_path))
        with pytest.raises(Exception):
            cache.init_data()
