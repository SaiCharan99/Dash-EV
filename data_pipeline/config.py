import os
from dotenv import load_dotenv

load_dotenv()

OE_API_KEY  = os.environ.get('OE_API_KEY', '')
NEM_REGIONS = ['NSW1', 'VIC1', 'QLD1', 'SA1', 'TAS1']
DATE_START  = '2015-01-01'
DATE_END    = '2024-12-31'

FUEL_TECHS = [
    'coal_black', 'coal_brown',
    'gas_ccgt', 'gas_ocgt',
    'solar_utility', 'solar_rooftop',
    'wind', 'hydro',
    'battery_discharging',
]

SOURCE_CATEGORY = {
    'coal_black':          'fossil',
    'coal_brown':          'fossil',
    'gas_ccgt':            'fossil',
    'gas_ocgt':            'fossil',
    'solar_utility':       'renewable',
    'solar_rooftop':       'renewable',
    'wind':                'renewable',
    'hydro':               'renewable',
    'battery_discharging': 'storage',
}

AU_SEASONS = {
    12: 'summer', 1: 'summer', 2: 'summer',
     3: 'autumn', 4: 'autumn', 5: 'autumn',
     6: 'winter', 7: 'winter', 8: 'winter',
     9: 'spring',10: 'spring',11: 'spring',
}

# CSIRO GenCost 2024-25 published LCOE ranges ($/MWh)
LCOE_CSIRO = {
    'solar_utility': {'low': 44,  'mid': 54,  'high': 65},
    'wind_onshore':  {'low': 49,  'mid': 55,  'high': 61},
    'coal_black':    {'low': 80,  'mid': 100, 'high': 130},
    'gas_ccgt':      {'low': 70,  'mid': 82,  'high': 95},
    'gas_ocgt':      {'low': 120, 'mid': 145, 'high': 180},
    'battery_2hr':   {'low': 100, 'mid': 125, 'high': 160},
}

# CSIRO GenCost forward estimates for 2030
LCOE_CSIRO_2030 = {
    'solar_utility': {'low': 27, 'mid': 40, 'high': 56},
    'wind_onshore':  {'low': 40, 'mid': 49, 'high': 59},
    'battery_2hr':   {'low': 60, 'mid': 80, 'high': 110},
}

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'energy')
RAW_DIR  = os.path.join(DATA_DIR, 'raw')
