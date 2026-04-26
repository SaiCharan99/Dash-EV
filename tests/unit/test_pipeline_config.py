"""
Unit tests for data_pipeline/config.py constants.
Verifies that LCOE values, season mapping, source categories, and paths are sane.
"""

import os
import pytest
from data_pipeline.config import (
    NEM_REGIONS, DATE_START, DATE_END, FUEL_TECHS, SOURCE_CATEGORY,
    AU_SEASONS, LCOE_CSIRO, LCOE_CSIRO_2030, DATA_DIR, RAW_DIR,
)


class TestNemRegions:
    def test_five_regions(self):
        assert len(NEM_REGIONS) == 5

    def test_region_codes(self):
        expected = {'NSW1', 'VIC1', 'QLD1', 'SA1', 'TAS1'}
        assert set(NEM_REGIONS) == expected


class TestDateRange:
    def test_start_before_end(self):
        from datetime import date
        start = date.fromisoformat(DATE_START)
        end   = date.fromisoformat(DATE_END)
        assert start < end

    def test_start_year(self):
        assert DATE_START.startswith('2015')

    def test_end_year(self):
        assert DATE_END.startswith('2024')


class TestFuelTechs:
    def test_not_empty(self):
        assert len(FUEL_TECHS) > 0

    def test_expected_techs_present(self):
        for tech in ('coal_black', 'gas_ccgt', 'solar_utility', 'wind', 'hydro'):
            assert tech in FUEL_TECHS, f'{tech} missing from FUEL_TECHS'

    def test_all_lowercase_underscored(self):
        for t in FUEL_TECHS:
            assert t == t.lower(), f'{t} should be lowercase'
            assert ' ' not in t, f'{t} should use underscores not spaces'


class TestSourceCategory:
    def test_all_fuel_techs_have_category(self):
        for tech in FUEL_TECHS:
            assert tech in SOURCE_CATEGORY, f'{tech} has no SOURCE_CATEGORY entry'

    def test_categories_are_valid(self):
        valid = {'fossil', 'renewable', 'storage'}
        for tech, cat in SOURCE_CATEGORY.items():
            assert cat in valid, f'{tech}: invalid category {cat!r}'

    def test_coal_is_fossil(self):
        assert SOURCE_CATEGORY['coal_black'] == 'fossil'

    def test_solar_is_renewable(self):
        assert SOURCE_CATEGORY['solar_utility'] == 'renewable'

    def test_battery_is_storage(self):
        assert SOURCE_CATEGORY['battery_discharging'] == 'storage'


class TestAuSeasons:
    def test_all_twelve_months_covered(self):
        assert set(AU_SEASONS.keys()) == set(range(1, 13))

    def test_season_values_are_valid(self):
        valid = {'summer', 'autumn', 'winter', 'spring'}
        assert set(AU_SEASONS.values()) == valid

    def test_december_is_summer(self):
        assert AU_SEASONS[12] == 'summer'

    def test_june_is_winter(self):
        assert AU_SEASONS[6] == 'winter'

    def test_march_is_autumn(self):
        assert AU_SEASONS[3] == 'autumn'

    def test_september_is_spring(self):
        assert AU_SEASONS[9] == 'spring'


class TestLcoeConstants:
    def test_required_technologies(self):
        required = {'solar_utility', 'wind_onshore', 'coal_black', 'gas_ccgt', 'gas_ocgt', 'battery_2hr'}
        assert required.issubset(LCOE_CSIRO.keys())

    def test_each_tech_has_low_mid_high(self):
        for tech, vals in LCOE_CSIRO.items():
            assert 'low' in vals and 'mid' in vals and 'high' in vals, \
                f'{tech} missing low/mid/high'

    def test_lcoe_ordering(self):
        for tech, vals in LCOE_CSIRO.items():
            assert vals['low'] <= vals['mid'] <= vals['high'], \
                f'{tech}: low={vals["low"]} mid={vals["mid"]} high={vals["high"]} must be ordered'

    def test_solar_cheaper_than_coal(self):
        assert LCOE_CSIRO['solar_utility']['mid'] < LCOE_CSIRO['coal_black']['mid']

    def test_2030_projections_have_ordering(self):
        for tech, vals in LCOE_CSIRO_2030.items():
            assert vals['low'] <= vals['mid'] <= vals['high'], \
                f'{tech} 2030: ordering violated'

    def test_2030_solar_cheaper_than_current(self):
        assert LCOE_CSIRO_2030['solar_utility']['mid'] < LCOE_CSIRO['solar_utility']['mid']


class TestPaths:
    def test_data_dir_is_absolute_or_relative(self):
        assert os.path.isabs(os.path.normpath(DATA_DIR)) or DATA_DIR.startswith('..')

    def test_raw_dir_is_inside_data_dir(self):
        assert os.path.normpath(RAW_DIR).startswith(os.path.normpath(DATA_DIR))
