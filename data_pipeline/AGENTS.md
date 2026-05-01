# data_pipeline/ — Energy Data Pipeline

Run once locally to produce parquet files consumed by the dashboard at runtime.

## Three-step flow

```
Step 1a (real):      01_fetch_openelectricity.py  →  data/energy/raw/*.parquet
Step 1b (synthetic): 01_generate_synthetic_data.py →  data/energy/raw/*.parquet
Step 2:              02_clean_and_aggregate.py      →  data/energy/*.parquet (4 canonical files)
```

Use `01_generate_synthetic_data.py` without an API key. Use `01_fetch_openelectricity.py` for real AEMO data (requires `OE_API_KEY` in `.env`).

## config.py — constants shared with the rest of the app

- `NEM_REGIONS` — `['NSW1','VIC1','QLD1','SA1','TAS1']` (raw API codes; cleaned to `NSW` etc. after pipeline)
- `FUEL_TECHS` — 9 fuel technology strings (same keys used in parquet `source` column)
- `SOURCE_CATEGORY` — maps fuel tech → `'fossil'` / `'renewable'` / `'storage'`
- `AU_SEASONS` — month int → season string (`12,1,2` → `'summer'`, etc.)
- `LCOE_CSIRO` — CSIRO GenCost 2024-25 published ranges `{tech: {low, mid, high}}` in $/MWh
- `LCOE_CSIRO_2030` — forward estimates for 2030
- `DATA_DIR` / `RAW_DIR` — resolved paths to `data/energy/` and `data/energy/raw/`

## Output parquet schemas

### demand_by_region.parquet
`region, year, month, season, demand_gwh, peak_demand_gw`

### generation_by_source.parquet
`region, year, month, season, source, source_category, generation_gwh, capacity_gw, capacity_factor`

### prices_by_region.parquet
`region, year, month, season, avg_spot_mwh, max_spot_mwh, min_spot_mwh`

### lcoe_estimates.parquet
`technology, year, lcoe_low, lcoe_mid, lcoe_high, is_projection, source`  
Built entirely from `LCOE_CSIRO` / `LCOE_CSIRO_2030` constants — no API calls. Years 2025+ have `is_projection=True`.

## Notes

- Region codes are normalised from `NSW1` → `NSW` during pipeline step 2.
- Rooftop solar data quality is unreliable before 2015; pipeline enforces `DATE_START = '2015-01-01'`.
- Monthly interval (`1M`) used for all API fetches; requires ~5 chunked requests to cover 2015–2024 (API limit ~2 years per request).
