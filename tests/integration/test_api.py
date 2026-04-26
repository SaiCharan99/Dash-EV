"""
Integration tests for FastAPI REST endpoints.

Requires real parquet files in data/energy/ (run data pipeline first).
Tests are skipped automatically if parquet files are missing.

Fixtures: api_client (session-scoped, from conftest.py)
"""

import pytest


class TestHealth:
    def test_health_ok(self, api_client):
        r = api_client.get('/api/health')
        assert r.status_code == 200
        body = r.json()
        assert body['status'] == 'ok'
        assert body['data_loaded'] is True


class TestDemandEndpoint:
    def test_default_returns_records(self, api_client):
        r = api_client.get('/api/energy/demand')
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_region_filter(self, api_client):
        r = api_client.get('/api/energy/demand?region=NSW')
        assert r.status_code == 200
        for row in r.json():
            assert row['region'] == 'NSW'

    def test_year_range_filter(self, api_client):
        r = api_client.get('/api/energy/demand?year_from=2020&year_to=2022')
        assert r.status_code == 200
        for row in r.json():
            assert 2020 <= row['year'] <= 2022

    def test_season_filter(self, api_client):
        r = api_client.get('/api/energy/demand?season=summer')
        assert r.status_code == 200
        for row in r.json():
            assert row['season'] == 'summer'

    def test_combined_filters(self, api_client):
        r = api_client.get('/api/energy/demand?region=VIC&year_from=2020&year_to=2023&season=winter')
        assert r.status_code == 200
        for row in r.json():
            assert row['region'] == 'VIC'
            assert 2020 <= row['year'] <= 2023
            assert row['season'] == 'winter'

    def test_record_schema(self, api_client):
        r = api_client.get('/api/energy/demand?region=SA&year_from=2022&year_to=2022')
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 0
        row = data[0]
        for key in ('region', 'year', 'month', 'season', 'demand_gwh'):
            assert key in row, f'Missing key: {key}'

    def test_invalid_year_param(self, api_client):
        r = api_client.get('/api/energy/demand?year_from=1990')
        assert r.status_code == 422

    def test_unknown_region_returns_empty(self, api_client):
        r = api_client.get('/api/energy/demand?region=FAKE')
        assert r.status_code == 200
        assert r.json() == []


class TestGenerationEndpoint:
    def test_default_returns_records(self, api_client):
        r = api_client.get('/api/energy/generation')
        assert r.status_code == 200
        assert len(r.json()) > 0

    def test_source_filter(self, api_client):
        r = api_client.get('/api/energy/generation?source=solar_utility')
        assert r.status_code == 200
        for row in r.json():
            assert row['source'] == 'solar_utility'

    def test_region_and_source_filter(self, api_client):
        r = api_client.get('/api/energy/generation?region=QLD&source=wind')
        assert r.status_code == 200
        for row in r.json():
            assert row['region'] == 'QLD'
            assert row['source'] == 'wind'

    def test_record_schema(self, api_client):
        r = api_client.get('/api/energy/generation?region=NSW&year_from=2022&year_to=2022')
        data = r.json()
        if data:
            row = data[0]
            for key in ('region', 'year', 'month', 'source', 'source_category', 'generation_gwh'):
                assert key in row


class TestPricesEndpoint:
    def test_default_returns_records(self, api_client):
        r = api_client.get('/api/energy/prices')
        assert r.status_code == 200
        assert len(r.json()) > 0

    def test_region_filter(self, api_client):
        r = api_client.get('/api/energy/prices?region=TAS')
        assert r.status_code == 200
        for row in r.json():
            assert row['region'] == 'TAS'

    def test_prices_non_negative(self, api_client):
        r = api_client.get('/api/energy/prices')
        for row in r.json():
            assert row['avg_spot_mwh'] >= 0


class TestLcoeEndpoint:
    def test_returns_records(self, api_client):
        r = api_client.get('/api/energy/lcoe')
        assert r.status_code == 200
        assert len(r.json()) > 0

    def test_technology_filter(self, api_client):
        r = api_client.get('/api/energy/lcoe?technology=solar_utility')
        assert r.status_code == 200
        for row in r.json():
            assert row['technology'] == 'solar_utility'

    def test_year_filter(self, api_client):
        r = api_client.get('/api/energy/lcoe?year=2024')
        assert r.status_code == 200
        for row in r.json():
            assert row['year'] == 2024

    def test_lcoe_ordering_in_response(self, api_client):
        r = api_client.get('/api/energy/lcoe?technology=solar_utility')
        for row in r.json():
            assert row['lcoe_low'] <= row['lcoe_mid'] <= row['lcoe_high']

    def test_projection_flag(self, api_client):
        r = api_client.get('/api/energy/lcoe?year=2030')
        data = r.json()
        if data:
            for row in data:
                assert row['is_projection'] is True

    def test_history_not_projected(self, api_client):
        r = api_client.get('/api/energy/lcoe?year=2020')
        data = r.json()
        if data:
            for row in data:
                assert row['is_projection'] is False


class TestSummaryEndpoint:
    def test_nsw_summary(self, api_client):
        r = api_client.get('/api/energy/summary/NSW')
        assert r.status_code == 200
        body = r.json()
        assert body['region'] == 'NSW'
        assert body['peak_demand_gw'] > 0
        assert body['total_twh'] > 0
        assert 0 <= body['renewable_pct'] <= 100
        assert body['avg_price_mwh'] > 0
        assert isinstance(body['top_source'], str)

    def test_all_regions_return_200(self, api_client):
        for region in ['NSW', 'VIC', 'QLD', 'SA', 'TAS']:
            r = api_client.get(f'/api/energy/summary/{region}')
            assert r.status_code == 200, f'{region} summary failed'

    def test_unknown_region_404(self, api_client):
        r = api_client.get('/api/energy/summary/FAKE')
        assert r.status_code == 404

    def test_case_insensitive_region(self, api_client):
        r = api_client.get('/api/energy/summary/nsw')
        assert r.status_code == 200
        assert r.json()['region'] == 'NSW'


class TestHealthNoData:
    def test_health_reports_not_loaded(self, api_client_no_data):
        r = api_client_no_data.get('/api/health')
        assert r.status_code == 200
        assert r.json()['data_loaded'] is False

    def test_demand_503_when_no_data(self, api_client_no_data):
        r = api_client_no_data.get('/api/energy/demand')
        assert r.status_code == 503
