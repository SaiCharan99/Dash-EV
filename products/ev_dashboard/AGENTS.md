# products/ev_dashboard/ — EV Market Intelligence Dashboard

Dash app at `/ev/`. Visualises Washington State EV registration data (~280k rows).

## Data loading

`data.py` loads the CSV **at import time** (module top-level, not lazily). The app is ready immediately but startup is slightly slower.

```
data/ev_population.csv  →  _raw (pd.DataFrame)  →  DF (2015–2025 filtered)
```

### Key exports from data.py

| Name | Type | Description |
|------|------|-------------|
| `DF` | DataFrame | Cleaned registrations, 2015–2025 |
| `ALL_MAKES` | list[str] | `['All'] + sorted makes` |
| `YEARS_WA` | list[int] | Distinct model years in DF |
| `WA_COUNTIES` | dict | `{county: (lat, lon)}` — 39 WA counties |
| `df_battery` | DataFrame | Battery cost + range trends 2013–2025 (hardcoded) |
| `df_global` | DataFrame | Global EV sales by country/year (hardcoded) |
| `_filter(yr_range, ev_type, make)` | fn | Main filter — returns subset of DF |

### Column names after cleaning

`Year`, `Make`, `Model`, `Type` (BEV/PHEV/Other), `Range`, `County`, `City`, `Utility`, `EV_Type_Full`

## Filter bar inputs (shared across all EV callbacks)

| Dash ID | Type | Values |
|---------|------|--------|
| `ev-yr-range` | RangeSlider | `[2015, 2025]` |
| `ev-type-filter` | RadioItems | `'All'` / `'BEV'` / `'PHEV'` |
| `ev-make-filter` | Dropdown | `ALL_MAKES` list |

## Tab structure

All tabs and callbacks are defined in `app.py` (single file, not split into separate callback modules). Tabs: **Overview · Make & Model · Range · Geography · Global Context**.

## Non-obvious decisions

- `ALL_MAKES` includes `'All'` as the first element so dropdown default works without special-casing.
- `WA_COUNTIES` coords are approximate county centroids used only for scatter-geo bubble placement.
- Global sales (`GLOBAL_SALES`) and battery data (`BATTERY`) are hardcoded dicts, not loaded from files.
