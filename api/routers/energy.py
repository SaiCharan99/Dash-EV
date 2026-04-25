from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import pandas as pd
from api.cache import get_demand_df, get_generation_df, get_prices_df, get_lcoe_df

router = APIRouter(tags=['energy'])


def _require(df, name='data'):
    if df is None:
        raise HTTPException(503, detail=f'{name} not loaded — run data pipeline first')
    return df


@router.get('/demand')
def get_demand(
    region:    Optional[str] = Query(None, description='NSW|VIC|QLD|SA|TAS'),
    year_from: int           = Query(2015, ge=2015, le=2024),
    year_to:   int           = Query(2024, ge=2015, le=2024),
    season:    Optional[str] = Query(None, description='summer|autumn|winter|spring'),
):
    df = _require(get_demand_df(), 'demand')
    df = df[(df.year >= year_from) & (df.year <= year_to)]
    if region:
        df = df[df.region == region.upper()]
    if season:
        df = df[df.season == season.lower()]
    return df.to_dict(orient='records')


@router.get('/generation')
def get_generation(
    region:    Optional[str] = Query(None),
    source:    Optional[str] = Query(None),
    year_from: int           = Query(2015, ge=2015, le=2024),
    year_to:   int           = Query(2024, ge=2015, le=2024),
):
    df = _require(get_generation_df(), 'generation')
    df = df[(df.year >= year_from) & (df.year <= year_to)]
    if region:
        df = df[df.region == region.upper()]
    if source:
        df = df[df.source == source.lower()]
    return df.to_dict(orient='records')


@router.get('/prices')
def get_prices(
    region:    Optional[str] = Query(None),
    year_from: int           = Query(2015, ge=2015, le=2024),
    year_to:   int           = Query(2024, ge=2015, le=2024),
):
    df = _require(get_prices_df(), 'prices')
    df = df[(df.year >= year_from) & (df.year <= year_to)]
    if region:
        df = df[df.region == region.upper()]
    return df.to_dict(orient='records')


@router.get('/lcoe')
def get_lcoe(
    technology: Optional[str] = Query(None),
    year:       Optional[int] = Query(None),
):
    df = _require(get_lcoe_df(), 'lcoe')
    if technology:
        df = df[df.technology == technology]
    if year:
        df = df[df.year == year]
    return df.to_dict(orient='records')


@router.get('/summary/{region}')
def get_region_summary(region: str):
    region = region.upper()
    dem = _require(get_demand_df(), 'demand')
    gen = _require(get_generation_df(), 'generation')
    pri = _require(get_prices_df(), 'prices')

    d = dem[dem.region == region]
    g = gen[gen.region == region]
    p = pri[pri.region == region]

    if d.empty:
        raise HTTPException(404, detail=f'Region {region} not found')

    peak_gw = float(d['demand_gwh'].max() / (24 * 30))
    total_twh = float(d['demand_gwh'].sum() / 1000)

    renewable_gen = g[g.source_category == 'renewable']['generation_gwh'].sum()
    total_gen     = g['generation_gwh'].sum()
    renewable_pct = float(renewable_gen / total_gen * 100) if total_gen else 0

    avg_price = float(p['avg_spot_mwh'].mean()) if not p.empty else 0

    top_source = (
        g.groupby('source')['generation_gwh'].sum()
        .sort_values(ascending=False)
        .index[0] if not g.empty else 'N/A'
    )

    return {
        'region':        region,
        'peak_demand_gw': round(peak_gw, 2),
        'total_twh':     round(total_twh, 1),
        'renewable_pct': round(renewable_pct, 1),
        'avg_price_mwh': round(avg_price, 2),
        'top_source':    top_source,
    }
