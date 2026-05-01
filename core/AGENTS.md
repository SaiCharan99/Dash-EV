# core/ — Shared Design System

Five small modules. Import from here rather than from individual files.

## Modules

### design_tokens.py — color constants
All hex/rgba values used across both dashboards. Apple-inspired palette.

**Backgrounds:** `BG` `PANEL` `BG2`  
**Text:** `TEXT` `SECONDARY` `MUTED` `SUBTLE`  
**Borders:** `SEP` `CARD_BORDER` `CARD_SHADOW`  
**Accent colors:** `BLUE` `GREEN` `ORANGE` `RED` `PURPLE` `TEAL`  
**Chart palette:** `PALETTE` (15-color list, starts with BLUE)  
**Energy semantics:** `ENERGY_SOLAR` `ENERGY_WIND` `ENERGY_COAL` `ENERGY_GAS` `ENERGY_HYDRO` `ENERGY_BATT`  
**Energy dicts:** `ENERGY_SOURCE_COLORS` `ENERGY_SOURCE_LABELS` (keyed by fuel tech string)

### chart_factory.py — Plotly layout helpers

- `_chart(height=320) -> dict` — base Plotly layout dict (Inter font, white bg, grey grid, hover style)
- `_dual_axis_chart(height=320) -> dict` — adds `yaxis2` overlaid on right side
- `_rgba(hex, alpha) -> str` — hex + alpha → `rgba(r,g,b,a)` string
- `_bar_h(x_vals, y_vals, color, hover_tmpl, min_alpha=0.22) -> go.Bar` — horizontal bar; linear opacity gradient from `min_alpha` (shortest bar) to `1.0` (longest). Data must be sorted ascending before passing.

### layout_helpers.py — Dash UI components

- `_panel(children, flex=1, extra=None)` — white card with border-radius 18px + shadow; wraps in `className='dash-card'`
- `_row(*children, gap, mb, className)` — flex row; default `className='ev-row'` (use `'en-row'` for energy)
- `_ph(title, subtitle='')` — panel header: bold title + muted subtitle, `padding: 20px 20px 0`
- `_kpi(label, vid, did, accent=BLUE)` — full KPI tile component with value/delta div IDs + accent bar
- `_legend_row(items)` — `[(color, label, pct), ...]` → coloured dot + text legend
- `_pill_label(text, label_id=None)` — uppercase 10px filter label above inputs

### app_cache.py — Flask-Cache singleton
`flask_cache = Cache()` — initialised by energy dashboard's Flask server. Import this instance; do not create another.

### dash_utils.py — HTML template
`ACCESSIBLE_INDEX` — Dash `index_string` with `<html lang="en">` for WCAG compliance. Assign to `app.index_string` in each Dash app.
