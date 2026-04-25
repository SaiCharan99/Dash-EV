from api.cache import get_demand_df, get_generation_df, get_prices_df, get_lcoe_df
from data_pipeline.config import SOURCE_CATEGORY, AU_SEASONS

NEM_REGIONS   = ['NSW', 'VIC', 'QLD', 'SA', 'TAS']
REGION_LABELS = {'NSW': 'New South Wales', 'VIC': 'Victoria',
                 'QLD': 'Queensland', 'SA': 'South Australia', 'TAS': 'Tasmania'}
REGION_COORDS = {
    'NSW': (-31.9,  146.9),
    'VIC': (-36.9,  144.3),
    'QLD': (-22.6,  144.1),
    'SA':  (-30.0,  135.8),
    'TAS': (-41.9,  146.4),
}

FUEL_ORDER = [
    'coal_black', 'coal_brown', 'gas_ccgt', 'gas_ocgt',
    'hydro', 'wind', 'solar_utility', 'solar_rooftop', 'battery_discharging',
]

SEASONS = ['summer', 'autumn', 'winter', 'spring']


def filter_demand(regions=None, yr_range=(2015, 2024), season=None):
    df = get_demand_df()
    if df is None:
        return None
    df = df[(df.year >= yr_range[0]) & (df.year <= yr_range[1])]
    if regions:
        df = df[df.region.isin(regions)]
    if season and season != 'All':
        df = df[df.season == season.lower()]
    return df


def filter_generation(regions=None, yr_range=(2015, 2024), sources=None, season=None):
    df = get_generation_df()
    if df is None:
        return None
    df = df[(df.year >= yr_range[0]) & (df.year <= yr_range[1])]
    if regions:
        df = df[df.region.isin(regions)]
    if sources:
        df = df[df.source.isin(sources)]
    if season and season != 'All':
        df = df[df.season == season.lower()]
    return df


def filter_prices(regions=None, yr_range=(2015, 2024)):
    df = get_prices_df()
    if df is None:
        return None
    df = df[(df.year >= yr_range[0]) & (df.year <= yr_range[1])]
    if regions:
        df = df[df.region.isin(regions)]
    return df
