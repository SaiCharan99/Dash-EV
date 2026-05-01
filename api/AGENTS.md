# api/ — Data Cache + REST Routers

## cache.py — in-memory data store

Four module-level DataFrames loaded once at startup by `main.py`'s lifespan hook:

| Accessor | Parquet file | Key columns |
|----------|-------------|-------------|
| `get_demand_df()` | `demand_by_region.parquet` | region, year, month, season, demand_gwh, peak_demand_gw |
| `get_generation_df()` | `generation_by_source.parquet` | region, year, month, season, source, source_category, generation_gwh, capacity_gw, capacity_factor |
| `get_prices_df()` | `prices_by_region.parquet` | region, year, month, season, avg_spot_mwh, max_spot_mwh, min_spot_mwh |
| `get_lcoe_df()` | `lcoe_estimates.parquet` | technology, year, lcoe_low, lcoe_mid, lcoe_high, is_projection, source |

`init_data()` — loads all four. Called by `main.py`; gracefully skips if parquet files are absent.  
`is_ready() -> bool` — True when demand_df is loaded. Used by `/api/health`.

**Dash callbacks call these directly** (no HTTP round-trip). REST endpoints call the same functions and serialise to JSON.

## routers/health.py
`GET /api/health` → `{"status": "ok", "data_loaded": bool}`

## routers/energy.py — REST endpoints

| Method + Path | Query params | Returns |
|---------------|-------------|---------|
| `GET /api/energy/demand` | `region`, `year_from`, `year_to`, `season` | demand rows |
| `GET /api/energy/generation` | `region`, `source`, `year_from`, `year_to`, `season` | generation rows |
| `GET /api/energy/prices` | `region`, `year_from`, `year_to` | price rows |
| `GET /api/energy/lcoe` | `technology` | LCOE range rows |
| `GET /api/energy/summary/{region}` | — | KPIs: peak_gw, renewable_pct, avg_price, top_source |

All endpoints raise HTTP 503 if data not loaded. Raises HTTP 404 for unknown region in summary.
