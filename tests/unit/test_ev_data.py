"""
Unit tests for products/ev_dashboard/data.py.
These tests require ev_population.csv to be present at data/ev_population.csv.
Tests are skipped automatically if the file is missing.
"""

import os
import sys
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CSV_PATH = os.path.join(ROOT, 'data', 'ev_population.csv')

pytestmark = pytest.mark.skipif(
    not os.path.exists(CSV_PATH),
    reason='ev_population.csv not present — place file at data/ev_population.csv'
)


@pytest.fixture(scope='module')
def ev_data():
    from products.ev_dashboard.data import DF, ALL_MAKES, YEARS_WA, _filter, df_global, df_battery
    return {
        'DF': DF, 'ALL_MAKES': ALL_MAKES, 'YEARS_WA': YEARS_WA,
        '_filter': _filter, 'df_global': df_global, 'df_battery': df_battery,
    }


class TestDataLoad:
    def test_df_is_not_empty(self, ev_data):
        assert len(ev_data['DF']) > 0

    def test_df_year_range(self, ev_data):
        df = ev_data['DF']
        assert df['Year'].min() >= 2015
        assert df['Year'].max() <= 2025

    def test_required_columns(self, ev_data):
        df = ev_data['DF']
        for col in ('Year', 'Make', 'Model', 'Type', 'Range', 'County'):
            assert col in df.columns, f'Missing column: {col}'

    def test_type_values(self, ev_data):
        types = set(ev_data['DF']['Type'].unique())
        assert 'BEV' in types or 'PHEV' in types

    def test_all_makes_starts_with_all(self, ev_data):
        assert ev_data['ALL_MAKES'][0] == 'All'

    def test_all_makes_sorted(self, ev_data):
        makes = ev_data['ALL_MAKES'][1:]
        assert makes == sorted(makes)

    def test_years_wa_sorted(self, ev_data):
        yw = ev_data['YEARS_WA']
        assert yw == sorted(yw)


class TestFilterFunction:
    def test_filter_year_range(self, ev_data):
        df = ev_data['_filter']([2020, 2022], 'All', 'All')
        assert df['Year'].min() >= 2020
        assert df['Year'].max() <= 2022

    def test_filter_bev_type(self, ev_data):
        df = ev_data['_filter']([2015, 2025], 'BEV', 'All')
        assert (df['Type'] == 'BEV').all()

    def test_filter_phev_type(self, ev_data):
        df = ev_data['_filter']([2015, 2025], 'PHEV', 'All')
        assert (df['Type'] == 'PHEV').all()

    def test_filter_all_type_returns_both(self, ev_data):
        all_df = ev_data['_filter']([2015, 2025], 'All', 'All')
        bev_df = ev_data['_filter']([2015, 2025], 'BEV', 'All')
        phev_df = ev_data['_filter']([2015, 2025], 'PHEV', 'All')
        assert len(all_df) >= len(bev_df)
        assert len(all_df) >= len(phev_df)

    def test_filter_make(self, ev_data):
        makes = ev_data['ALL_MAKES']
        if len(makes) > 1:
            target_make = makes[1]
            df = ev_data['_filter']([2015, 2025], 'All', target_make)
            assert (df['Make'] == target_make).all()

    def test_filter_empty_when_out_of_range(self, ev_data):
        df = ev_data['_filter']([2100, 2100], 'All', 'All')
        assert len(df) == 0


class TestGlobalData:
    def test_df_global_not_empty(self, ev_data):
        assert len(ev_data['df_global']) > 0

    def test_df_global_columns(self, ev_data):
        df = ev_data['df_global']
        for col in ('Year', 'Country', 'Region', 'Total'):
            assert col in df.columns

    def test_df_global_year_range(self, ev_data):
        df = ev_data['df_global']
        assert df['Year'].min() >= 2015
        assert df['Year'].max() <= 2024

    def test_df_battery_columns(self, ev_data):
        df = ev_data['df_battery']
        for col in ('Year', 'Cost_kWh', 'Avg_Range_km'):
            assert col in df.columns

    def test_battery_cost_declining(self, ev_data):
        df = ev_data['df_battery'].sort_values('Year')
        costs = df['Cost_kWh'].tolist()
        assert costs[0] > costs[-1], 'Battery cost should decline over time'


class TestWaCounties:
    def test_wa_counties_not_empty(self):
        from products.ev_dashboard.data import WA_COUNTIES
        assert len(WA_COUNTIES) > 30

    def test_wa_counties_has_king(self):
        from products.ev_dashboard.data import WA_COUNTIES
        assert 'King' in WA_COUNTIES

    def test_wa_counties_coords_valid(self):
        from products.ev_dashboard.data import WA_COUNTIES
        for county, (lat, lon) in WA_COUNTIES.items():
            assert 45 <= lat <= 49, f'{county}: lat {lat} out of WA range'
            assert -125 <= lon <= -116, f'{county}: lon {lon} out of WA range'
