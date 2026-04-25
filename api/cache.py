import os
import pandas as pd

_demand_df     = None
_generation_df = None
_prices_df     = None
_lcoe_df       = None

_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'energy')


def init_data():
    global _demand_df, _generation_df, _prices_df, _lcoe_df
    _demand_df     = pd.read_parquet(os.path.join(_DATA_DIR, 'demand_by_region.parquet'))
    _generation_df = pd.read_parquet(os.path.join(_DATA_DIR, 'generation_by_source.parquet'))
    _prices_df     = pd.read_parquet(os.path.join(_DATA_DIR, 'prices_by_region.parquet'))
    _lcoe_df       = pd.read_parquet(os.path.join(_DATA_DIR, 'lcoe_estimates.parquet'))


def get_demand_df()     -> pd.DataFrame: return _demand_df
def get_generation_df() -> pd.DataFrame: return _generation_df
def get_prices_df()     -> pd.DataFrame: return _prices_df
def get_lcoe_df()       -> pd.DataFrame: return _lcoe_df


def is_ready() -> bool:
    return _demand_df is not None
