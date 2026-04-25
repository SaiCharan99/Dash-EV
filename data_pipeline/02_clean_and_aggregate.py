"""
Clean raw parquet files from 01_fetch_openelectricity.py and produce
4 canonical parquet files consumed by the dashboard:

    data/energy/demand_by_region.parquet
    data/energy/generation_by_source.parquet
    data/energy/prices_by_region.parquet
    data/energy/lcoe_estimates.parquet

Usage:
    python data_pipeline/02_clean_and_aggregate.py
"""

import os
import sys
import calendar
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from data_pipeline.config import (
    AU_SEASONS, SOURCE_CATEGORY, FUEL_TECHS,
    LCOE_CSIRO, LCOE_CSIRO_2030, RAW_DIR, DATA_DIR,
)

os.makedirs(DATA_DIR, exist_ok=True)


def _add_time_cols(df, ts_col='timestamp'):
    df[ts_col] = pd.to_datetime(df[ts_col], utc=True)
    df['year']   = df[ts_col].dt.year
    df['month']  = df[ts_col].dt.month
    df['season'] = df['month'].map(AU_SEASONS)
    return df


# ── 1. Demand ────────────────────────────────────────────────────────────────

raw_demand_path = os.path.join(RAW_DIR, 'raw_demand.parquet')

if os.path.exists(raw_demand_path):
    raw = pd.read_parquet(raw_demand_path)
    if 'demand_gwh' in raw.columns:
        # synthetic format — already aggregated
        agg = raw[raw.year.between(2015, 2024)]
    else:
        raw = _add_time_cols(raw)
        # get_market() demand_energy returns values already in GWh
        agg = (raw
               .groupby(['region', 'year', 'month', 'season'])
               .agg(demand_gwh=('value', 'sum'))
               .reset_index())
        agg['peak_demand_gw'] = agg['demand_gwh'] / (agg['month'].map(
            lambda m: calendar.monthrange(2023, m)[1]) * 24) * 1.2
        agg = agg[agg.year >= 2015]
    agg.to_parquet(os.path.join(DATA_DIR, 'demand_by_region.parquet'), index=False)
    print(f'demand_by_region.parquet  →  {len(agg)} rows')
else:
    print('raw_demand.parquet not found — skipping demand')


# ── 2. Generation ─────────────────────────────────────────────────────────────

raw_gen_path = os.path.join(RAW_DIR, 'raw_generation.parquet')
raw_fac_path = os.path.join(RAW_DIR, 'raw_facilities.parquet')

if os.path.exists(raw_gen_path):
    raw = pd.read_parquet(raw_gen_path)
    if 'generation_gwh' in raw.columns:
        # synthetic format — already aggregated
        agg = raw[raw.year.between(2015, 2024)]
    else:
        raw = _add_time_cols(raw)
        raw = raw.rename(columns={'name': 'source'})
        raw['source'] = raw['source'].str.lower().str.replace(' ', '_')
        raw = raw[raw.source.isin(FUEL_TECHS)]
        raw['source_category'] = raw['source'].map(SOURCE_CATEGORY).fillna('other')
        agg = (raw
               .groupby(['region', 'year', 'month', 'season', 'source', 'source_category'])
               .agg(generation_gwh=('value', lambda x: x.sum() / 1000))
               .reset_index())
        if os.path.exists(raw_fac_path):
            fac = pd.read_parquet(raw_fac_path)
            fac.columns = [c.lower() for c in fac.columns]
            region_col = next((c for c in fac.columns if 'region' in c), None)
            cap_col    = next((c for c in fac.columns if 'capacity' in c), None)
            fuel_col   = next((c for c in fac.columns if 'fuel' in c or 'tech' in c), None)
            if region_col and cap_col and fuel_col:
                cap = (fac.groupby([region_col, fuel_col])[cap_col]
                       .sum().reset_index()
                       .rename(columns={region_col: 'region', fuel_col: 'source', cap_col: 'capacity_mw'}))
                cap['region'] = cap['region'].str.replace('1', '')
                cap['source'] = cap['source'].str.lower().str.replace(' ', '_')
                cap['capacity_gw'] = cap['capacity_mw'] / 1000
                agg = agg.merge(cap[['region', 'source', 'capacity_gw']], on=['region', 'source'], how='left')
            else:
                agg['capacity_gw'] = np.nan
        else:
            agg['capacity_gw'] = np.nan
        agg['hours'] = agg['month'].map(lambda m: calendar.monthrange(2023, m)[1] * 24)
        agg['capacity_factor'] = np.where(
            agg['capacity_gw'] > 0,
            agg['generation_gwh'] / (agg['capacity_gw'] * agg['hours']),
            np.nan,
        )
        agg = agg.drop(columns=['hours'])
        agg = agg[agg.year >= 2015]
    agg.to_parquet(os.path.join(DATA_DIR, 'generation_by_source.parquet'), index=False)
    print(f'generation_by_source.parquet  →  {len(agg)} rows')
else:
    print('raw_generation.parquet not found — skipping generation')


# ── 3. Prices ─────────────────────────────────────────────────────────────────

raw_price_path = os.path.join(RAW_DIR, 'raw_prices.parquet')

if os.path.exists(raw_price_path):
    raw = pd.read_parquet(raw_price_path)
    if 'avg_spot_mwh' in raw.columns:
        # synthetic format — already aggregated
        agg = raw[raw.year.between(2015, 2024)]
    else:
        raw = _add_time_cols(raw)
        agg = (raw
               .groupby(['region', 'year', 'month', 'season'])
               .agg(avg_spot_mwh=('value', 'mean'),
                    max_spot_mwh=('value', 'max'),
                    min_spot_mwh=('value', 'min'))
               .reset_index())
        agg = agg[agg.year >= 2015]
    agg.to_parquet(os.path.join(DATA_DIR, 'prices_by_region.parquet'), index=False)
    print(f'prices_by_region.parquet  →  {len(agg)} rows')
else:
    print('raw_prices.parquet not found — skipping prices')


# ── 4. LCOE estimates (from CSIRO constants — no API needed) ──────────────────

rows = []
for tech, vals in LCOE_CSIRO.items():
    # interpolate linearly from 2015 values back from 2024 mid
    # LCOE for coal/gas was roughly 10–20% higher in 2015
    fossil = tech in ('coal_black', 'gas_ccgt', 'gas_ocgt')
    for yr in range(2015, 2025):
        t = (yr - 2015) / 9
        if tech == 'solar_utility':
            # solar dropped dramatically: 2015 ~$200 → 2024 $54 mid
            mid  = 200 * (1 - t) + vals['mid'] * t
            low  = 160 * (1 - t) + vals['low'] * t
            high = 250 * (1 - t) + vals['high'] * t
        elif tech == 'wind_onshore':
            mid  = 90 * (1 - t) + vals['mid'] * t
            low  = 70 * (1 - t) + vals['low'] * t
            high = 115 * (1 - t) + vals['high'] * t
        elif tech == 'battery_2hr':
            mid  = 400 * (1 - t) + vals['mid'] * t
            low  = 320 * (1 - t) + vals['low'] * t
            high = 500 * (1 - t) + vals['high'] * t
        else:
            mid  = vals['mid']  * (1 + 0.05 * (1 - t))
            low  = vals['low']  * (1 + 0.05 * (1 - t))
            high = vals['high'] * (1 + 0.05 * (1 - t))
        rows.append(dict(technology=tech, year=yr,
                         lcoe_low=round(low, 1), lcoe_mid=round(mid, 1),
                         lcoe_high=round(high, 1), is_projection=False,
                         source='CSIRO_GenCost_2024'))

for tech, vals in {**LCOE_CSIRO, **LCOE_CSIRO_2030}.items():
    if tech not in LCOE_CSIRO_2030:
        proj_vals = {'low': LCOE_CSIRO[tech]['low'] * 0.9,
                     'mid': LCOE_CSIRO[tech]['mid'] * 0.9,
                     'high': LCOE_CSIRO[tech]['high'] * 0.9}
    else:
        proj_vals = LCOE_CSIRO_2030[tech]
    base = LCOE_CSIRO.get(tech, LCOE_CSIRO_2030.get(tech, {}))
    for yr in range(2025, 2031):
        t = (yr - 2025) / 5
        rows.append(dict(
            technology=tech, year=yr,
            lcoe_low=round(base.get('low', proj_vals['low']) * (1 - t) + proj_vals['low'] * t, 1),
            lcoe_mid=round(base.get('mid', proj_vals['mid']) * (1 - t) + proj_vals['mid'] * t, 1),
            lcoe_high=round(base.get('high', proj_vals['high']) * (1 - t) + proj_vals['high'] * t, 1),
            is_projection=True,
            source='CSIRO_GenCost_2024',
        ))

lcoe_df = pd.DataFrame(rows)
lcoe_df.to_parquet(os.path.join(DATA_DIR, 'lcoe_estimates.parquet'), index=False)
print(f'lcoe_estimates.parquet  →  {len(lcoe_df)} rows')

print('\nAll done. Parquet files are in data/energy/')
