"""
Shared pytest fixtures for all test layers.

Session-scoped fixtures are expensive (parquet load, app startup) — they run once.
Function-scoped fixtures reset per test for isolation.
"""

import os
import sys
import pytest
import numpy as np
import pandas as pd

# Ensure project root is on the path regardless of cwd
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ── Minimal synthetic DataFrames (no file I/O) ────────────────────────────────

@pytest.fixture(scope='session')
def demand_df():
    rows = []
    for region in ['NSW', 'VIC', 'QLD', 'SA', 'TAS']:
        for year in range(2015, 2025):
            for month in range(1, 13):
                rows.append({
                    'region': region, 'year': year, 'month': month,
                    'season': _month_season(month),
                    'demand_gwh': 5000 + np.random.default_rng(42).integers(-500, 500),
                    'peak_demand_gw': 8.5,
                })
    return pd.DataFrame(rows)


@pytest.fixture(scope='session')
def generation_df():
    sources = ['coal_black', 'gas_ccgt', 'solar_utility', 'wind', 'hydro']
    cats = {
        'coal_black': 'fossil', 'gas_ccgt': 'fossil',
        'solar_utility': 'renewable', 'wind': 'renewable', 'hydro': 'renewable',
    }
    rows = []
    for region in ['NSW', 'VIC', 'QLD', 'SA', 'TAS']:
        for year in range(2015, 2025):
            for month in range(1, 13):
                for source in sources:
                    rows.append({
                        'region': region, 'year': year, 'month': month,
                        'season': _month_season(month),
                        'source': source,
                        'source_category': cats[source],
                        'generation_gwh': 800.0,
                        'capacity_gw': 2.0,
                        'capacity_factor': 0.18,
                    })
    return pd.DataFrame(rows)


@pytest.fixture(scope='session')
def prices_df():
    rows = []
    for region in ['NSW', 'VIC', 'QLD', 'SA', 'TAS']:
        for year in range(2015, 2025):
            for month in range(1, 13):
                rows.append({
                    'region': region, 'year': year, 'month': month,
                    'season': _month_season(month),
                    'avg_spot_mwh': 80.0 + (year - 2015) * 5,
                    'max_spot_mwh': 200.0,
                    'min_spot_mwh': 30.0,
                })
    return pd.DataFrame(rows)


@pytest.fixture(scope='session')
def lcoe_df():
    techs = ['solar_utility', 'wind_onshore', 'coal_black', 'gas_ccgt', 'gas_ocgt', 'battery_2hr']
    rows = []
    for tech in techs:
        for year in range(2015, 2031):
            rows.append({
                'technology': tech, 'year': year,
                'lcoe_low': 44.0, 'lcoe_mid': 54.0, 'lcoe_high': 65.0,
                'is_projection': year >= 2025,
                'source': 'CSIRO_GenCost_2024',
            })
    return pd.DataFrame(rows)


@pytest.fixture(scope='function')
def patched_cache(demand_df, generation_df, prices_df, lcoe_df, monkeypatch):
    """Inject in-memory DataFrames into api.cache without touching disk."""
    import api.cache as cache
    monkeypatch.setattr(cache, '_demand_df',     demand_df)
    monkeypatch.setattr(cache, '_generation_df', generation_df)
    monkeypatch.setattr(cache, '_prices_df',     prices_df)
    monkeypatch.setattr(cache, '_lcoe_df',       lcoe_df)


@pytest.fixture(scope='session')
def real_cache():
    """
    Load real parquet files if they exist; skip otherwise.
    Use for integration / e2e tests that need production-quality data.
    """
    from api.cache import init_data, is_ready
    data_dir = os.path.join(ROOT, 'data', 'energy')
    required = [
        'demand_by_region.parquet',
        'generation_by_source.parquet',
        'prices_by_region.parquet',
        'lcoe_estimates.parquet',
    ]
    missing = [f for f in required if not os.path.exists(os.path.join(data_dir, f))]
    if missing:
        pytest.skip(f'Parquet files not found: {missing}. Run data pipeline first.')
    init_data()
    assert is_ready()


@pytest.fixture(scope='session')
def api_client(real_cache):
    """FastAPI TestClient with real data loaded."""
    from fastapi.testclient import TestClient
    import main
    return TestClient(main.app, raise_server_exceptions=True)


@pytest.fixture(scope='session')
def api_client_no_data():
    """FastAPI TestClient without loading parquet files (tests 503 behaviour)."""
    from fastapi.testclient import TestClient
    import api.cache as cache
    cache._demand_df = cache._generation_df = cache._prices_df = cache._lcoe_df = None
    import main
    return TestClient(main.app)


# ── Helper ─────────────────────────────────────────────────────────────────────

def _month_season(m):
    return {
        12: 'summer', 1: 'summer', 2: 'summer',
         3: 'autumn', 4: 'autumn', 5: 'autumn',
         6: 'winter', 7: 'winter', 8: 'winter',
         9: 'spring',10: 'spring',11: 'spring',
    }[m]
