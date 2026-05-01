# Dash Trial — Energy Platform

## Architecture

FastAPI server (`main.py`) mounts three Dash apps via `WSGIMiddleware`:

```
/          → landing/app.py        (static product cards)
/ev/       → products/ev_dashboard/app.py   (WA EV data, ~280k rows CSV)
/energy/   → products/energy_dashboard/app.py (AU NEM data, parquet files)
/api/      → FastAPI REST endpoints
/api/docs  → Swagger UI
```

Mount order matters — more specific paths registered first (`/ev`, `/energy`, then `/`).

## How to run

```bash
uvicorn main:app --port 8050 --reload
# or
python main.py
```

Energy data must be available before starting:
```bash
python data_pipeline/01_generate_synthetic_data.py   # synthetic, no API key needed
# or
python data_pipeline/01_fetch_openelectricity.py     # real AEMO data, needs OE_API_KEY in .env
python data_pipeline/02_clean_and_aggregate.py
```

## Key directories

| Path | Purpose |
|------|---------|
| `core/` | Shared design tokens, Plotly layout helpers, Dash UI components |
| `api/` | Data cache (loaded at startup) + FastAPI REST routers |
| `products/ev_dashboard/` | Product 1: WA EV registrations dashboard |
| `products/energy_dashboard/` | Product 2: AU energy transition dashboard |
| `landing/` | Home page — no callbacks, static only |
| `data_pipeline/` | Scripts to fetch + clean energy data into parquet |
| `data/energy/` | Four parquet files (gitignored) consumed at runtime |
| `assets/` | `style.css` (shared across all apps), SVG icons |

## Data flow

```
data_pipeline/01_*.py  →  data/energy/raw/*.parquet
data_pipeline/02_clean_and_aggregate.py  →  data/energy/*.parquet (4 canonical files)
main.py lifespan → api/cache.init_data() loads parquet into RAM
products/energy_dashboard/callbacks/*.py → call api/cache.get_*_df() directly (no HTTP)
api/routers/energy.py → same accessors, serialised to JSON for external consumers
```

## Non-obvious decisions

- All three Dash apps share `assets/style.css` via their `assets_folder` pointing to the repo root `assets/`.
- EV dashboard loads CSV at import time (`products/ev_dashboard/data.py` top-level). Energy dashboard loads lazily via `api/cache`.
- Component IDs are namespaced by product: `ev-*` / `dem-*` / `gen-*` / `econ-*` / `ren-*` / `sc-*` / `en-*` to avoid Dash callback collisions when all apps share a server.
- `core/app_cache.py` holds a single Flask-Cache instance initialised by the energy dashboard's Flask server; EV dashboard does not use server-side caching.
