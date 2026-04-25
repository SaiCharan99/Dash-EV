import os
import pandas as pd

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ev_population.csv')

_raw = pd.read_csv(DATA_PATH, low_memory=False)
_raw.columns = [c.strip() for c in _raw.columns]
_raw = _raw.rename(columns={
    'Electric Vehicle Type': 'EV_Type_Full',
    'Electric Range':        'Range',
    'Model Year':            'Year',
    'Electric Utility':      'Utility',
})
_raw['Type']  = _raw['EV_Type_Full'].map({
    'Battery Electric Vehicle (BEV)':         'BEV',
    'Plug-in Hybrid Electric Vehicle (PHEV)': 'PHEV',
}).fillna('Other')
_raw['Make']  = _raw['Make'].str.strip().str.title()
_raw['Model'] = _raw['Model'].str.strip().str.title()

DF        = _raw[_raw['Year'].between(2015, 2025)].copy()
ALL_MAKES = ['All'] + sorted(DF['Make'].dropna().unique().tolist())
YEARS_WA  = sorted(DF['Year'].unique().tolist())

WA_COUNTIES = {
    'Adams':(46.97,-118.56),'Asotin':(46.34,-117.37),'Benton':(46.22,-119.39),
    'Chelan':(47.82,-120.62),'Clallam':(48.10,-123.80),'Clark':(45.79,-122.49),
    'Columbia':(46.31,-117.95),'Cowlitz':(46.20,-122.77),'Douglas':(47.63,-119.81),
    'Ferry':(48.60,-118.55),'Franklin':(46.55,-119.07),'Garfield':(46.43,-117.58),
    'Grant':(47.22,-119.45),'Grays Harbor':(47.14,-123.81),'Island':(48.23,-122.55),
    'Jefferson':(47.82,-124.10),'King':(47.49,-121.83),'Kitsap':(47.61,-122.65),
    'Kittitas':(47.12,-120.73),'Klickitat':(45.87,-120.75),'Lewis':(46.57,-122.42),
    'Lincoln':(47.58,-118.40),'Mason':(47.35,-123.22),'Okanogan':(48.55,-119.71),
    'Pacific':(46.57,-123.91),'Pend Oreille':(48.55,-117.43),'Pierce':(47.11,-122.09),
    'San Juan':(48.54,-122.96),'Skagit':(48.42,-121.76),'Skamania':(45.82,-121.93),
    'Snohomish':(48.04,-121.76),'Spokane':(47.62,-117.43),'Stevens':(48.35,-117.79),
    'Thurston':(46.97,-122.85),'Wahkiakum':(46.30,-123.43),'Walla Walla':(46.27,-118.37),
    'Whatcom':(48.84,-122.11),'Whitman':(46.90,-117.40),'Yakima':(46.65,-120.45),
}

GLOBAL_YEARS = list(range(2015, 2025))
GLOBAL_REGIONS = {
    'Asia-Pacific': ['China','Japan','South Korea','India'],
    'Europe':       ['Germany','Norway','UK','France','Netherlands','Sweden','Rest of EU'],
    'Americas':     ['USA'],
    'Rest of World':['Rest of World'],
}
GLOBAL_SALES = {
    'China':        [0.33,0.51,0.78,1.26,1.21,1.37,3.30,5.90,8.10,9.80],
    'USA':          [0.11,0.16,0.20,0.36,0.33,0.33,0.65,0.92,1.40,1.60],
    'Germany':      [0.023,0.025,0.055,0.067,0.108,0.395,0.356,0.471,0.524,0.580],
    'Norway':       [0.025,0.029,0.033,0.046,0.056,0.076,0.118,0.138,0.163,0.175],
    'UK':           [0.015,0.025,0.047,0.060,0.075,0.175,0.267,0.267,0.314,0.350],
    'France':       [0.022,0.022,0.036,0.044,0.061,0.186,0.219,0.210,0.245,0.280],
    'Netherlands':  [0.043,0.024,0.011,0.025,0.068,0.098,0.170,0.230,0.250,0.270],
    'South Korea':  [0.011,0.013,0.026,0.031,0.038,0.056,0.103,0.163,0.210,0.250],
    'Japan':        [0.050,0.048,0.054,0.059,0.071,0.098,0.130,0.145,0.170,0.200],
    'India':        [0.002,0.003,0.004,0.006,0.008,0.015,0.040,0.085,0.150,0.210],
    'Rest of EU':   [0.015,0.020,0.030,0.045,0.065,0.180,0.280,0.340,0.380,0.420],
    'Rest of World':[0.008,0.012,0.018,0.025,0.035,0.060,0.110,0.180,0.260,0.340],
}
BATTERY = dict(
    Year         =[2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025],
    Cost_kWh     =[680, 540, 373, 295, 230, 185, 156, 137, 132, 138, 139, 115, 100],
    Avg_Range_km =[180, 195, 215, 240, 265, 290, 320, 355, 385, 415, 450, 490, 530],
)
df_battery = pd.DataFrame(BATTERY)

def _get_region(c):
    return next((r for r, cs in GLOBAL_REGIONS.items() if c in cs), 'Rest of World')

df_global = pd.DataFrame([
    dict(Year=y, Country=c, Region=_get_region(c), Total=v)
    for c, vs in GLOBAL_SALES.items()
    for y, v in zip(GLOBAL_YEARS, vs)
])


def _filter(yr_range, ev_type, make):
    yr0, yr1 = yr_range
    d = DF[(DF['Year'] >= yr0) & (DF['Year'] <= yr1)]
    if ev_type != 'All':
        d = d[d['Type'] == ev_type]
    if make != 'All':
        d = d[d['Make'] == make]
    return d
