# energy_dashboard/callbacks/ — Tab Callback Modules

Each file registers one tab's callbacks via `register(app)`. All registered in `products/energy_dashboard/app.py`.

## Shared filter bar inputs (used by every callback)

| Dash ID | Type | Values |
|---------|------|--------|
| `en-yr-slider` | RangeSlider | `[2015, 2024]` — year range tuple |
| `en-region-filter` | Dropdown multi | list of `['NSW','VIC','QLD','SA','TAS']` |
| `en-season-filter` | RadioItems | `'All'` / `'Summer'` / `'Autumn'` / `'Winter'` / `'Spring'` |

## cb_kpis.py — KPI strip (always visible)
Outputs: `en-kpi-total`, `en-kpi-peak`, `en-kpi-renew`, `en-kpi-price`, `en-kpi-yoy`  
Data: `filter_demand()` + `filter_generation()` + `filter_prices()`

## cb_demand.py — Demand tab
Outputs: `dem-timeseries`, `dem-seasonal-box`, `dem-heatmap`  
Data: `filter_demand()`

## cb_generation.py — Generation Mix tab
Outputs: `gen-trend-lines`, `gen-stacked-bar`, `gen-donut`, `gen-donut-legend`, `gen-monthly-area`  
Data: `filter_generation()`  
Note: donut legend is a separate `html.Div` output built alongside the donut chart.

## cb_economics.py — Economics & LCOE tab
Outputs: `econ-lcoe-range`, `econ-lcoe-trend`, `econ-price-vs-lcoe`, `econ-demand-cost`  
Data: `get_lcoe_df()` (CSIRO constants) + `filter_prices()` + `filter_demand()`

## cb_renewables.py — Renewables Growth tab
Outputs: `ren-share-bar`, `ren-cf-heatmap`, `ren-growth-waterfall`  
Data: `filter_generation()`

## cb_comparison.py — State Comparison tab
Outputs: `sc-grouped-bar`, `sc-radar`, `sc-price-map`  
Data: `filter_generation()` + `filter_prices()` + `filter_demand()`  
Note: `sc-price-map` uses `REGION_COORDS` from `products/energy_dashboard/data.py` for bubble positions.

## Pattern used in every callback

```python
from products.energy_dashboard.data import filter_demand, filter_generation, filter_prices
from core.chart_factory import _chart, _rgba, _dual_axis_chart
from core.design_tokens import ENERGY_SOURCE_COLORS, ENERGY_SOURCE_LABELS, ...

def register(app):
    @app.callback(Output(...), Input('en-yr-slider','value'), ...)
    def _cb(yr_range, regions, season):
        df = filter_demand(regions, yr_range, season)
        if df is None or df.empty:
            return go.Figure()
        ...
```
