"""
Generate realistic synthetic Australian energy data (2015–2024).

Based on published AEMO Annual Reports, AER State of the Energy Market,
and OpenNEM published aggregates. The energy transition trends (coal decline,
solar/wind rise, 2022 price spike) are calibrated to match documented statistics.

Usage:
    python data_pipeline/01_generate_synthetic_data.py
"""

import os
import sys
import calendar
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from data_pipeline.config import AU_SEASONS, SOURCE_CATEGORY, RAW_DIR, DATA_DIR

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

rng = np.random.default_rng(42)

YEARS  = list(range(2015, 2025))
MONTHS = list(range(1, 13))

# ── Seasonal demand multipliers (AU southern hemisphere) ─────────────────────
# Summer (Dec-Feb): peak cooling load; Winter (Jun-Aug): peak heating
_SEASON_DEMAND = {
    1: 1.08, 2: 1.06, 3: 0.98, 4: 0.93,
    5: 0.95, 6: 1.05, 7: 1.10, 8: 1.07,
    9: 0.96, 10: 0.93, 11: 0.97, 12: 1.10,
}

# ── Base monthly demand (GWh) per region — anchored to AEMO 2019 actuals ─────
_BASE_DEMAND_GWH = {
    'NSW': 6400,
    'VIC': 4400,
    'QLD': 4800,
    'SA':  1250,
    'TAS': 820,
}

# Mild demand trend: ~-0.5%/yr efficiency gains, offset by population growth
_DEMAND_TREND = {
    'NSW': -0.003, 'VIC': -0.005, 'QLD': +0.005, 'SA': -0.005, 'TAS': -0.002,
}

# ── Generation mix share trajectories ────────────────────────────────────────
# Format: {source: (share_2015, share_2024)}
# Shares will be linearly interpolated; some have non-linear curves for solar
_MIX = {
    'NSW': {
        'coal_black':          (0.76, 0.44),
        'gas_ccgt':            (0.06, 0.05),
        'gas_ocgt':            (0.04, 0.03),
        'solar_utility':       (0.00, 0.13),
        'solar_rooftop':       (0.01, 0.12),
        'wind':                (0.02, 0.10),
        'hydro':               (0.07, 0.08),
        'battery_discharging': (0.00, 0.02),
        'coal_brown':          (0.00, 0.00),
    },
    'VIC': {
        'coal_brown':          (0.70, 0.38),
        'coal_black':          (0.00, 0.00),
        'gas_ccgt':            (0.06, 0.06),
        'gas_ocgt':            (0.03, 0.03),
        'solar_utility':       (0.00, 0.11),
        'solar_rooftop':       (0.01, 0.13),
        'wind':                (0.08, 0.18),
        'hydro':               (0.04, 0.06),
        'battery_discharging': (0.00, 0.02),
    },
    'QLD': {
        'coal_black':          (0.66, 0.43),
        'coal_brown':          (0.00, 0.00),
        'gas_ccgt':            (0.10, 0.07),
        'gas_ocgt':            (0.07, 0.05),
        'solar_utility':       (0.00, 0.18),
        'solar_rooftop':       (0.02, 0.15),
        'wind':                (0.00, 0.06),
        'hydro':               (0.04, 0.04),
        'battery_discharging': (0.00, 0.01),
    },
    'SA': {
        'coal_black':          (0.00, 0.00),
        'coal_brown':          (0.00, 0.00),
        'gas_ccgt':            (0.22, 0.12),
        'gas_ocgt':            (0.18, 0.10),
        'solar_utility':       (0.04, 0.28),
        'solar_rooftop':       (0.03, 0.18),
        'wind':                (0.32, 0.28),
        'hydro':               (0.00, 0.00),
        'battery_discharging': (0.00, 0.04),
    },
    'TAS': {
        'coal_black':          (0.00, 0.00),
        'coal_brown':          (0.00, 0.00),
        'gas_ccgt':            (0.00, 0.00),
        'gas_ocgt':            (0.04, 0.05),
        'solar_utility':       (0.00, 0.01),
        'solar_rooftop':       (0.00, 0.03),
        'wind':                (0.12, 0.16),
        'hydro':               (0.84, 0.75),
        'battery_discharging': (0.00, 0.00),
    },
}

# Solar utility grows faster than linear (exponential adoption post-2019)
def _solar_share(base, end, yr, accel=2.5):
    t = (yr - 2015) / 9
    t_curved = t ** (1 / accel)
    return base + (end - base) * t_curved

# Seasonal solar capacity factor multipliers (utility scale)
_SOLAR_SEASON = {
    1: 1.45, 2: 1.35, 3: 1.10, 4: 0.85,
    5: 0.65, 6: 0.55, 7: 0.60, 8: 0.75,
    9: 1.00, 10: 1.20, 11: 1.35, 12: 1.50,
}
# Wind seasonal multipliers
_WIND_SEASON = {
    1: 0.85, 2: 0.88, 3: 0.95, 4: 1.05,
    5: 1.10, 6: 1.15, 7: 1.18, 8: 1.12,
    9: 1.05, 10: 0.95, 11: 0.90, 12: 0.88,
}

# ── Installed capacity (GW) per region × source — AEMO 2024 snapshot ─────────
_CAPACITY_GW = {
    'NSW': {'coal_black': 7.0, 'gas_ccgt': 1.5, 'gas_ocgt': 1.2,
            'solar_utility': 4.5, 'solar_rooftop': 4.8, 'wind': 1.8,
            'hydro': 2.0, 'battery_discharging': 0.6, 'coal_brown': 0.0},
    'VIC': {'coal_brown': 3.8, 'gas_ccgt': 1.2, 'gas_ocgt': 0.8,
            'solar_utility': 3.2, 'solar_rooftop': 4.5, 'wind': 3.0,
            'hydro': 1.0, 'battery_discharging': 0.5, 'coal_black': 0.0},
    'QLD': {'coal_black': 9.0, 'gas_ccgt': 2.5, 'gas_ocgt': 2.0,
            'solar_utility': 5.5, 'solar_rooftop': 5.0, 'wind': 0.9,
            'hydro': 0.7, 'battery_discharging': 0.3, 'coal_brown': 0.0},
    'SA':  {'gas_ccgt': 1.4, 'gas_ocgt': 1.2,
            'solar_utility': 2.8, 'solar_rooftop': 1.5, 'wind': 2.6,
            'battery_discharging': 0.4, 'coal_black': 0.0, 'coal_brown': 0.0,
            'hydro': 0.0},
    'TAS': {'hydro': 2.6, 'wind': 0.4, 'gas_ocgt': 0.2,
            'coal_black': 0.0, 'coal_brown': 0.0, 'gas_ccgt': 0.0,
            'solar_utility': 0.05, 'solar_rooftop': 0.2, 'battery_discharging': 0.0},
}

# ── Spot price baseline $/MWh per region ─────────────────────────────────────
_PRICE_BASE = {
    'NSW': 72, 'VIC': 70, 'QLD': 75, 'SA': 88, 'TAS': 68,
}
# Year-level price multipliers (2022 gas crisis spike)
_PRICE_YEAR = {
    2015: 0.82, 2016: 0.78, 2017: 0.98, 2018: 1.10,
    2019: 0.88, 2020: 0.75, 2021: 1.05, 2022: 2.20,
    2023: 1.35, 2024: 1.10,
}
_PRICE_SEASON = {
    1: 1.15, 2: 1.10, 3: 0.95, 4: 0.88,
    5: 0.90, 6: 1.05, 7: 1.12, 8: 1.08,
    9: 0.92, 10: 0.90, 11: 0.95, 12: 1.18,
}


def _interp(v0, v1, yr):
    t = (yr - 2015) / 9
    return v0 + (v1 - v0) * t


print('Generating synthetic NEM energy data (2015–2024)...')

demand_rows = []
generation_rows = []
price_rows = []

REGIONS = ['NSW', 'VIC', 'QLD', 'SA', 'TAS']

for region in REGIONS:
    base_d = _BASE_DEMAND_GWH[region]
    trend  = _DEMAND_TREND[region]
    mix    = _MIX[region]

    for yr in YEARS:
        yr_factor = (1 + trend) ** (yr - 2019)

        for mo in MONTHS:
            days    = calendar.monthrange(yr, mo)[1]
            hours   = days * 24
            season  = AU_SEASONS[mo]
            s_mult  = _SEASON_DEMAND[mo]
            noise   = rng.normal(1.0, 0.015)

            demand_gwh    = base_d * yr_factor * s_mult * noise
            peak_demand_gw = demand_gwh / hours * 1.35 * rng.uniform(1.0, 1.05)

            demand_rows.append(dict(
                region=region, year=yr, month=mo, season=season,
                demand_gwh=round(demand_gwh, 1),
                peak_demand_gw=round(peak_demand_gw, 3),
            ))

            # Generation mix for this month
            total_gen = demand_gwh * rng.uniform(1.02, 1.06)

            for src, (s0, s1) in mix.items():
                if src == 'solar_utility':
                    share = _solar_share(s0, s1, yr)
                else:
                    share = _interp(s0, s1, yr)

                # Apply seasonal shaping
                if 'solar' in src:
                    share_mo = share * _SOLAR_SEASON[mo]
                elif src == 'wind':
                    share_mo = share * _WIND_SEASON[mo]
                else:
                    share_mo = share

                gen_gwh = max(0.0, total_gen * share_mo * rng.uniform(0.97, 1.03))
                if gen_gwh < 0.5:
                    continue

                cap_gw = _CAPACITY_GW.get(region, {}).get(src, 0.0)
                if cap_gw > 0 and gen_gwh > 0:
                    cf = min(gen_gwh / (cap_gw * hours), 0.95)
                else:
                    cf = float('nan')

                generation_rows.append(dict(
                    region=region, year=yr, month=mo, season=season,
                    source=src,
                    source_category=SOURCE_CATEGORY.get(src, 'other'),
                    generation_gwh=round(gen_gwh, 2),
                    capacity_gw=cap_gw if cap_gw > 0 else float('nan'),
                    capacity_factor=round(cf, 4) if not np.isnan(cf) else float('nan'),
                ))

            # Spot price
            base_p  = _PRICE_BASE[region]
            avg_p   = base_p * _PRICE_YEAR[yr] * _PRICE_SEASON[mo] * rng.uniform(0.92, 1.08)
            max_p   = avg_p * rng.uniform(1.8, 3.5)
            min_p   = max(0.1, avg_p * rng.uniform(0.1, 0.4))

            price_rows.append(dict(
                region=region, year=yr, month=mo, season=season,
                avg_spot_mwh=round(avg_p, 2),
                max_spot_mwh=round(max_p, 2),
                min_spot_mwh=round(min_p, 2),
            ))


demand_df = pd.DataFrame(demand_rows)
gen_df    = pd.DataFrame(generation_rows)
price_df  = pd.DataFrame(price_rows)

demand_df.to_parquet(os.path.join(RAW_DIR, 'raw_demand.parquet'), index=False)
gen_df.to_parquet(os.path.join(RAW_DIR, 'raw_generation.parquet'), index=False)
price_df.to_parquet(os.path.join(RAW_DIR, 'raw_prices.parquet'), index=False)

print(f'raw_demand.parquet           → {len(demand_df)} rows')
print(f'raw_generation.parquet       → {len(gen_df)} rows')
print(f'raw_prices.parquet           → {len(price_df)} rows')

print('\nRaw files written to data/energy/raw/  →  now run:')
print('  python data_pipeline/02_clean_and_aggregate.py')
