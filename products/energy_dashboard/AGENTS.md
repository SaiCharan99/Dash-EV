# products/energy_dashboard/ — AU Energy Transition Dashboard

Dash app at `/energy/`. Visualises Australian NEM electricity data 2015–2024.

## App structure

`app.py` defines the layout and tab router. Callbacks are split into six modules under `callbacks/`, each registered via `register(app)`:

```python
# app.py bottom
_kpis.register(app)
_demand.register(app)
_generation.register(app)
_economics.register(app)
_renewables.register(app)
_comparison.register(app)
```

## Filter bar (always visible, inputs shared by all callbacks)

| Dash ID | Component | Default | Values |
|---------|-----------|---------|--------|
| `en-yr-slider` | RangeSlider | `[2015, 2024]` | year ints |
| `en-region-filter` | Dropdown multi | all 5 regions | `['NSW','VIC','QLD','SA','TAS']` |
| `en-season-filter` | RadioItems | `'All'` | `'All'` / `'Summer'` / `'Autumn'` / `'Winter'` / `'Spring'` |

## data.py — filter helpers

All callbacks use these three functions (not the raw `api.cache` accessors directly):

- `filter_demand(regions, yr_range, season)` — returns demand DataFrame subset
- `filter_generation(regions, yr_range, sources, season)` — returns generation subset
- `filter_prices(regions, yr_range)` — returns prices subset

All return `None` if data not yet loaded; callbacks must guard with `if df is None`.

### Reference constants

- `NEM_REGIONS` — `['NSW','VIC','QLD','SA','TAS']`
- `REGION_LABELS` — full state names keyed by code
- `REGION_COORDS` — `{region: (lat, lon)}` used for map bubble placement
- `FUEL_ORDER` — canonical fuel tech sort order for stacked charts
- `SEASONS` — `['summer','autumn','winter','spring']`

## KPI tile IDs (always rendered, outside tab content)

`en-kpi-total`, `en-kpi-peak`, `en-kpi-renew`, `en-kpi-price`, `en-kpi-yoy`

## Non-obvious decisions

- The KPI strip sits **outside** the tab router div (`en-tab-content`) so it updates on filter change regardless of which tab is active.
- Flask-Cache (`core/app_cache.flask_cache`) is initialised by this app's Flask server — not the EV app's.
- Energy source colors intentionally de-emphasise fossil fuels: coal/gas use muted greys (`ENERGY_COAL`, `ENERGY_GAS`); solar uses gold, wind uses teal.
