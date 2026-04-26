"""
End-to-end pipeline tests.

These tests run the full data pipeline (01_generate_synthetic_data.py →
02_clean_and_aggregate.py) in a temp directory and verify that the produced
parquet files have the correct schemas, row counts, and data quality.

No external API key is needed — uses the synthetic generator only.
"""

import os
import sys
import shutil
import subprocess
import pytest
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


@pytest.fixture(scope='module')
def pipeline_output(tmp_path_factory):
    """
    Runs both pipeline scripts with DATA_DIR and RAW_DIR pointing to a temp
    directory. Returns the path to the temp data/energy/ directory.
    """
    tmp = tmp_path_factory.mktemp('energy_data')
    raw_dir  = tmp / 'raw'
    raw_dir.mkdir()

    env = os.environ.copy()
    env['PIPELINE_DATA_DIR'] = str(tmp)
    env['PIPELINE_RAW_DIR']  = str(raw_dir)

    # We patch config by monkey-patching at subprocess level using env vars.
    # Simpler: run via Python directly in the same process using importlib.
    # We temporarily redirect config paths and re-import the pipeline modules.

    # Step 1 — generate synthetic data
    _run_generator(str(tmp), str(raw_dir))

    # Step 2 — clean and aggregate
    _run_cleaner(str(tmp), str(raw_dir))

    return tmp


def _run_generator(data_dir, raw_dir):
    """Import and execute 01_generate_synthetic_data with patched paths."""
    import importlib, types
    import data_pipeline.config as cfg_mod

    orig_data = cfg_mod.DATA_DIR
    orig_raw  = cfg_mod.RAW_DIR
    cfg_mod.DATA_DIR = data_dir
    cfg_mod.RAW_DIR  = raw_dir
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    try:
        spec = importlib.util.spec_from_file_location(
            'gen_synth',
            os.path.join(ROOT, 'data_pipeline', '01_generate_synthetic_data.py')
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        cfg_mod.DATA_DIR = orig_data
        cfg_mod.RAW_DIR  = orig_raw


def _run_cleaner(data_dir, raw_dir):
    """Import and execute 02_clean_and_aggregate with patched paths."""
    import importlib
    import data_pipeline.config as cfg_mod

    orig_data = cfg_mod.DATA_DIR
    orig_raw  = cfg_mod.RAW_DIR
    cfg_mod.DATA_DIR = data_dir
    cfg_mod.RAW_DIR  = raw_dir

    try:
        spec = importlib.util.spec_from_file_location(
            'clean_agg',
            os.path.join(ROOT, 'data_pipeline', '02_clean_and_aggregate.py')
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        cfg_mod.DATA_DIR = orig_data
        cfg_mod.RAW_DIR  = orig_raw


# ── Raw file checks ───────────────────────────────────────────────────────────

class TestRawFilesProduced:
    def test_raw_demand_exists(self, pipeline_output):
        assert (pipeline_output / 'raw' / 'raw_demand.parquet').exists()

    def test_raw_generation_exists(self, pipeline_output):
        assert (pipeline_output / 'raw' / 'raw_generation.parquet').exists()

    def test_raw_prices_exists(self, pipeline_output):
        assert (pipeline_output / 'raw' / 'raw_prices.parquet').exists()


# ── Final parquet checks ──────────────────────────────────────────────────────

class TestDemandParquet:
    @pytest.fixture(scope='class')
    def df(self, pipeline_output):
        return pd.read_parquet(pipeline_output / 'demand_by_region.parquet')

    def test_not_empty(self, df):
        assert len(df) > 0

    def test_columns(self, df):
        for col in ('region', 'year', 'month', 'season', 'demand_gwh'):
            assert col in df.columns

    def test_five_regions(self, df):
        assert set(df['region'].unique()) == {'NSW', 'VIC', 'QLD', 'SA', 'TAS'}

    def test_year_range(self, df):
        assert df['year'].min() >= 2015
        assert df['year'].max() <= 2024

    def test_twelve_months_per_region_year(self, df):
        counts = df.groupby(['region', 'year'])['month'].count()
        assert (counts == 12).all(), 'Expected 12 months per region-year'

    def test_demand_positive(self, df):
        assert (df['demand_gwh'] > 0).all()

    def test_seasons_valid(self, df):
        assert set(df['season'].unique()) == {'summer', 'autumn', 'winter', 'spring'}

    def test_nsw_demand_reasonable(self, df):
        nsw = df[df.region == 'NSW']
        avg_monthly = nsw['demand_gwh'].mean()
        # NSW consumes ~6000–7000 GWh/month historically
        assert 3000 < avg_monthly < 12000, f'NSW avg monthly demand {avg_monthly:.0f} GWh looks wrong'


class TestGenerationParquet:
    @pytest.fixture(scope='class')
    def df(self, pipeline_output):
        return pd.read_parquet(pipeline_output / 'generation_by_source.parquet')

    def test_not_empty(self, df):
        assert len(df) > 0

    def test_columns(self, df):
        for col in ('region', 'year', 'month', 'source', 'source_category', 'generation_gwh'):
            assert col in df.columns

    def test_source_categories(self, df):
        valid = {'fossil', 'renewable', 'storage'}
        assert set(df['source_category'].unique()).issubset(valid)

    def test_generation_non_negative(self, df):
        assert (df['generation_gwh'] >= 0).all()

    def test_coal_declines_over_time(self, df):
        coal = df[df.source == 'coal_black'].groupby('year')['generation_gwh'].sum()
        if len(coal) >= 2:
            assert coal.iloc[-1] < coal.iloc[0], 'Coal generation should decline 2015→2024'

    def test_solar_grows_over_time(self, df):
        solar = df[df.source == 'solar_utility'].groupby('year')['generation_gwh'].sum()
        if len(solar) >= 2:
            assert solar.iloc[-1] > solar.iloc[0], 'Solar generation should grow 2015→2024'

    def test_renewable_share_grows(self, df):
        annual = df.groupby(['year', 'source_category'])['generation_gwh'].sum().unstack(fill_value=0)
        total_col = annual.sum(axis=1)
        ren_col = annual.get('renewable', 0)
        ren_pct = ren_col / total_col * 100
        if len(ren_pct) >= 2:
            assert ren_pct.iloc[-1] > ren_pct.iloc[0], 'Renewable share should increase'


class TestPricesParquet:
    @pytest.fixture(scope='class')
    def df(self, pipeline_output):
        return pd.read_parquet(pipeline_output / 'prices_by_region.parquet')

    def test_not_empty(self, df):
        assert len(df) > 0

    def test_columns(self, df):
        for col in ('region', 'year', 'month', 'avg_spot_mwh'):
            assert col in df.columns

    def test_prices_positive(self, df):
        assert (df['avg_spot_mwh'] > 0).all()

    def test_2022_price_spike(self, df):
        avg_by_year = df.groupby('year')['avg_spot_mwh'].mean()
        if 2022 in avg_by_year.index and 2021 in avg_by_year.index:
            assert avg_by_year[2022] > avg_by_year[2021], \
                '2022 should show a price spike vs 2021 (gas crisis)'

    def test_max_gte_avg_gte_min(self, df):
        if 'max_spot_mwh' in df.columns and 'min_spot_mwh' in df.columns:
            assert (df['max_spot_mwh'] >= df['avg_spot_mwh']).all()
            assert (df['avg_spot_mwh'] >= df['min_spot_mwh']).all()


class TestLcoeParquet:
    @pytest.fixture(scope='class')
    def df(self, pipeline_output):
        return pd.read_parquet(pipeline_output / 'lcoe_estimates.parquet')

    def test_not_empty(self, df):
        assert len(df) > 0

    def test_columns(self, df):
        for col in ('technology', 'year', 'lcoe_low', 'lcoe_mid', 'lcoe_high', 'is_projection'):
            assert col in df.columns

    def test_year_range(self, df):
        assert df['year'].min() == 2015
        assert df['year'].max() == 2030

    def test_projections_post_2024(self, df):
        assert df[df['is_projection'] == True]['year'].min() == 2025
        assert df[df['is_projection'] == False]['year'].max() == 2024

    def test_solar_cheaper_than_coal_in_2024(self, df):
        solar_2024 = df[(df.technology == 'solar_utility') & (df.year == 2024)]['lcoe_mid'].values
        coal_2024  = df[(df.technology == 'coal_black')    & (df.year == 2024)]['lcoe_mid'].values
        if len(solar_2024) and len(coal_2024):
            assert solar_2024[0] < coal_2024[0]

    def test_ordering_low_mid_high(self, df):
        assert (df['lcoe_low'] <= df['lcoe_mid']).all()
        assert (df['lcoe_mid'] <= df['lcoe_high']).all()

    def test_source_is_csiro(self, df):
        assert (df['source'] == 'CSIRO_GenCost_2024').all()


# ── Cache loading after pipeline ─────────────────────────────────────────────

class TestCacheLoadFromPipeline:
    def test_init_data_loads_all_four_frames(self, pipeline_output, monkeypatch):
        import api.cache as cache
        monkeypatch.setattr(cache, '_DATA_DIR', str(pipeline_output))
        cache.init_data()
        assert cache.is_ready()
        assert cache.get_demand_df() is not None
        assert cache.get_generation_df() is not None
        assert cache.get_prices_df() is not None
        assert cache.get_lcoe_df() is not None

    def test_filter_demand_after_load(self, pipeline_output, monkeypatch):
        import api.cache as cache
        monkeypatch.setattr(cache, '_DATA_DIR', str(pipeline_output))
        cache.init_data()
        from products.energy_dashboard.data import filter_demand
        df = filter_demand(regions=['NSW'], yr_range=(2020, 2022))
        assert not df.empty
        assert set(df['region'].unique()) == {'NSW'}
