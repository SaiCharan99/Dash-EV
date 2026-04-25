"""
Fetch real NEM data from the OpenElectricity API and save raw parquet files
to data/energy/raw/.

Usage:
    python data_pipeline/01_fetch_openelectricity.py

Note: Free-tier API keys allow only the last 367 days of data.
      For full 2015-2024 history use 01_generate_synthetic_data.py instead.
"""

import os
import re
import sys
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

_NEM_REGION_RE = re.compile(r'(NSW|VIC|QLD|SA|TAS)1?')

import pandas as pd
from tqdm import tqdm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from data_pipeline.config import OE_API_KEY, NEM_REGIONS, RAW_DIR, DATA_DIR

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

if not OE_API_KEY:
    print('ERROR: OE_API_KEY not set. Add it to .env file.')
    sys.exit(1)

try:
    from openelectricity import OEClient
    from openelectricity.types import DataMetric, MarketMetric, UnitStatusType
except ImportError:
    print('ERROR: openelectricity package not installed. Run: pip install openelectricity')
    sys.exit(1)

client = OEClient(api_key=OE_API_KEY)

# Free plan allows ~367 days back. Probe the actual cutoff by trying a
# request and falling back to the safe window if we get a 400.
_TODAY      = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
_SAFE_START = _TODAY - timedelta(days=360)

from data_pipeline.config import DATE_START
_config_start = datetime.fromisoformat(DATE_START)
if _config_start < _SAFE_START:
    print(f'Note: DATE_START {DATE_START} is beyond the free-plan 367-day window.')
    print(f'      Fetching from {_SAFE_START.date()} to today ({_TODAY.date()}).')
    print('      Run 01_generate_synthetic_data.py for full 2015–2024 synthetic data.\n')

FETCH_START = max(_config_start, _SAFE_START)
FETCH_END   = _TODAY   # always fetch up to today so free-plan window is valid

CHUNK = 2   # years per request; single chunk covers free plan window fine


def _date_chunks(start: datetime, end: datetime, chunk_years: int = CHUNK):
    cur = start
    while cur < end:
        nxt = min(cur + relativedelta(years=chunk_years), end)
        yield cur, nxt
        cur = nxt + timedelta(days=1)


def _to_df(response) -> pd.DataFrame:
    """Parse OE API TimeSeriesResponse into a flat DataFrame.

    result.name examples:
      'demand_energy_NSW1'        → region=NSW, no fueltech
      'energy_NSW1|battery'       → region=NSW, fueltech=battery
      'price_NSW1'                → region=NSW, no fueltech

    result.data items: TimeSeriesDataPoint with .root = (datetime, float)
    """
    rows = []
    for ts in response.data:
        metric = ts.metric
        for result in ts.results:
            name = result.name
            # fueltech is always after '|' when present
            if '|' in name:
                name_prefix, raw_fuel = name.split('|', 1)
            else:
                name_prefix, raw_fuel = name, None

            # extract NEM region code (NSW/VIC/QLD/SA/TAS) from the name prefix
            m = _NEM_REGION_RE.search(name_prefix)
            region = m.group(1) if m else 'UNKNOWN'

            for pt in result.data:
                ts_val, value = pt.root
                row = {'timestamp': ts_val, 'metric': metric,
                       'value': value, 'region': region}
                if raw_fuel is not None:
                    row['name'] = raw_fuel
                rows.append(row)
    return pd.DataFrame(rows)


# ── Demand (market endpoint) ──────────────────────────────────────────────────
print('=== Fetching demand (demand_energy) ===')
demand_frames = []
for region in NEM_REGIONS:
    short = region.replace('1', '')
    chunks = list(_date_chunks(FETCH_START, FETCH_END))
    for s, e in tqdm(chunks, desc=short, total=len(chunks)):
        try:
            resp = client.get_market(
                network_code='NEM',
                metrics=[MarketMetric.DEMAND_ENERGY],
                interval='1M',
                network_region=region,
                date_start=s,
                date_end=e,
            )
            df = _to_df(resp)
            if not df.empty:
                demand_frames.append(df)
            time.sleep(0.3)
        except Exception as exc:
            print(f'  Warning: {region} {s.date()}–{e.date()}: {exc}')

if demand_frames:
    out = pd.concat(demand_frames, ignore_index=True)
    out.to_parquet(os.path.join(RAW_DIR, 'raw_demand.parquet'), index=False)
    print(f'  Saved raw_demand.parquet  ({len(out)} rows)\n')
else:
    print('  No demand data retrieved.\n')


# ── Generation by fuel type (network endpoint) ────────────────────────────────
print('=== Fetching generation (energy by fueltech) ===')
gen_frames = []
for region in NEM_REGIONS:
    short = region.replace('1', '')
    chunks = list(_date_chunks(FETCH_START, FETCH_END))
    for s, e in tqdm(chunks, desc=short, total=len(chunks)):
        try:
            resp = client.get_network_data(
                network_code='NEM',
                metrics=[DataMetric.ENERGY],
                interval='1M',
                network_region=region,
                secondary_grouping='fueltech',
                date_start=s,
                date_end=e,
            )
            df = _to_df(resp)
            if not df.empty:
                gen_frames.append(df)
            time.sleep(0.3)
        except Exception as exc:
            print(f'  Warning: {region} {s.date()}–{e.date()}: {exc}')

if gen_frames:
    out = pd.concat(gen_frames, ignore_index=True)
    out.to_parquet(os.path.join(RAW_DIR, 'raw_generation.parquet'), index=False)
    print(f'  Saved raw_generation.parquet  ({len(out)} rows)\n')
else:
    print('  No generation data retrieved.\n')


# ── Spot prices (market endpoint) ─────────────────────────────────────────────
print('=== Fetching spot prices ===')
price_frames = []
for region in NEM_REGIONS:
    short = region.replace('1', '')
    chunks = list(_date_chunks(FETCH_START, FETCH_END))
    for s, e in tqdm(chunks, desc=short, total=len(chunks)):
        try:
            resp = client.get_market(
                network_code='NEM',
                metrics=[MarketMetric.PRICE],
                interval='1M',
                network_region=region,
                date_start=s,
                date_end=e,
            )
            df = _to_df(resp)
            if not df.empty:
                price_frames.append(df)
            time.sleep(0.3)
        except Exception as exc:
            print(f'  Warning: {region} {s.date()}–{e.date()}: {exc}')

if price_frames:
    out = pd.concat(price_frames, ignore_index=True)
    out.to_parquet(os.path.join(RAW_DIR, 'raw_prices.parquet'), index=False)
    print(f'  Saved raw_prices.parquet  ({len(out)} rows)\n')
else:
    print('  No price data retrieved.\n')


# ── Facilities / installed capacity ───────────────────────────────────────────
print('=== Fetching facilities (installed capacity) ===')
try:
    fac_resp = client.get_facilities(
        network_id=['NEM'],
        status_id=[UnitStatusType.OPERATING],
    )
    fac_df = fac_resp.to_dataframe() if hasattr(fac_resp, 'to_dataframe') else pd.DataFrame(
        [u.__dict__ for u in fac_resp.facilities] if hasattr(fac_resp, 'facilities') else []
    )
    if not fac_df.empty:
        fac_df.to_parquet(os.path.join(RAW_DIR, 'raw_facilities.parquet'), index=False)
        print(f'  Saved raw_facilities.parquet  ({len(fac_df)} rows)\n')
    else:
        print('  Facilities response was empty.\n')
except Exception as exc:
    print(f'  Warning: facilities fetch failed: {exc}\n')

print('Done. Raw files are in data/energy/raw/')
print('Next step: python data_pipeline/02_clean_and_aggregate.py')
