# Energy Intelligence Platform

A two-product data analytics platform built with Python, FastAPI, and Dash.

---

## Products

### 1 · EV Market Intelligence
Washington State EV registration data from the Department of Licensing — 280,000+ vehicles, 2015–2025.

**What it shows:**
- Fleet composition by model year, BEV vs PHEV split
- Manufacturer market share and registration trends
- Model range distribution and volume vs range scatter
- County-level geographic distribution (bubble map)
- Global EV context: sales by region, battery cost decline, WA share of US market

<!-- Screenshot placeholder -->
<!-- ![EV Dashboard Overview](screenshots/ev_overview.png) -->
<!-- ![EV Geography Tab](screenshots/ev_geography.png) -->

---

### 2 · Australian Energy Transition
NEM region data (NSW, VIC, QLD, SA, TAS) covering 2015–2024, showing the shift from coal to renewables.

**What it shows:**
- Electricity demand patterns by region and season
- Generation mix evolution — coal decline vs solar/wind growth
- LCOE economics: CSIRO GenCost 2024-25 cost trajectories and spot price crossover
- Renewable penetration by state and capacity factor heatmaps
- State comparison: radar chart, grouped generation bar, Australia map

<!-- Screenshot placeholder -->
<!-- ![Energy Landing](screenshots/energy_landing.png) -->
<!-- ![Energy Generation Mix](screenshots/energy_generation.png) -->
<!-- ![Energy Economics](screenshots/energy_economics.png) -->

---

## Tech Stack

| Layer | Tools |
|---|---|
| Backend | FastAPI, uvicorn |
| Dashboards | Dash 2.17, Plotly |
| Data | pandas, pyarrow (parquet) |
| EV data | Washington State DOL (CSV) |
| Energy data | Synthetic (calibrated to AEMO) · Real API via OpenElectricity |
| LCOE data | CSIRO GenCost 2024-25 (hardcoded constants) |

---

## Project Structure

```
├── main.py                        # FastAPI entry point — mounts all apps
├── core/                          # Shared design system
│   ├── design_tokens.py           # Colours, palette
│   ├── chart_factory.py           # Plotly layout helpers
│   └── layout_helpers.py          # Dash panel/row/KPI components
├── landing/                       # Landing page at /
├── products/
│   ├── ev_dashboard/              # Product 1 — served at /ev/
│   └── energy_dashboard/          # Product 2 — served at /energy/
│       └── callbacks/             # One file per tab
├── api/
│   ├── cache.py                   # In-memory parquet store
│   └── routers/                   # REST endpoints /api/energy/*
├── data_pipeline/
│   ├── 01_generate_synthetic_data.py   # Generates realistic 2015–2024 NEM data
│   ├── 01_fetch_openelectricity.py     # Fetches real data (paid API plan needed)
│   ├── 02_clean_and_aggregate.py       # Cleans raw → final parquets
│   └── config.py
└── data/
    └── energy/                    # Parquet files loaded at startup
```

---

## Running Locally

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up environment

```bash
cp .env.example .env
# Add your OpenElectricity API key if using real data (optional)
# OE_API_KEY=your_key_here
```

### 3. Generate energy data

**Option A — Synthetic data (recommended, no API key needed):**
```bash
python data_pipeline/01_generate_synthetic_data.py
python data_pipeline/02_clean_and_aggregate.py
```

**Option B — Real API data (last 12 months, requires free API key from [openelectricity.org.au](https://platform.openelectricity.org.au)):**
```bash
python data_pipeline/01_fetch_openelectricity.py
python data_pipeline/02_clean_and_aggregate.py
```

### 4. Add EV data

Place `ev_population.csv` from [Washington State DOL](https://data.wa.gov/Transportation/Electric-Vehicle-Population-Data/f6w7-q2d2) into `data/`.

### 5. Start the server

```bash
python main.py
```

Then open:

| URL | Page |
|---|---|
| `http://localhost:8050` | Landing page |
| `http://localhost:8050/ev/` | EV Market Intelligence |
| `http://localhost:8050/energy/` | Australian Energy Transition |
| `http://localhost:8050/api/docs` | REST API (Swagger) |

---

## REST API

Available endpoints under `/api/energy/`:

```
GET /api/health
GET /api/energy/demand?region=NSW&year_from=2020&year_to=2024
GET /api/energy/generation?region=SA&source=solar_utility
GET /api/energy/prices?region=VIC&year_from=2022&year_to=2024
GET /api/energy/lcoe?technology=solar_utility
GET /api/energy/summary/{region}
```

---

## Data Sources

- **EV data** — Washington State Department of Licensing, [data.wa.gov](https://data.wa.gov)
- **Energy demand & generation** — AEMO via [OpenElectricity](https://openelectricity.org.au)
- **LCOE** — CSIRO GenCost 2024-25
- **Global EV sales** — IEA Global EV Outlook
- **Battery costs** — BloombergNEF
