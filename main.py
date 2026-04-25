import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware

from api.routers import energy, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    from api.cache import init_data, is_ready
    data_dir = os.path.join(os.path.dirname(__file__), 'data', 'energy')
    parquet_files = [
        'demand_by_region.parquet',
        'generation_by_source.parquet',
        'prices_by_region.parquet',
        'lcoe_estimates.parquet',
    ]
    if all(os.path.exists(os.path.join(data_dir, f)) for f in parquet_files):
        print('Loading energy data into cache...')
        init_data()
        print('Energy data loaded.')
    else:
        print('Energy parquet files not found — run data_pipeline/01_fetch_openelectricity.py first.')
        print('Energy dashboard will show empty charts until data is available.')
    yield


app = FastAPI(
    title='Energy Platform API',
    docs_url='/api/docs',
    redoc_url='/api/redoc',
    lifespan=lifespan,
)

app.include_router(health.router, prefix='/api')
app.include_router(energy.router, prefix='/api/energy')

from landing.app import server as landing_server
from products.ev_dashboard.app import server as ev_server
from products.energy_dashboard.app import server as energy_server

app.mount('/ev',     WSGIMiddleware(ev_server))
app.mount('/energy', WSGIMiddleware(energy_server))
app.mount('/',       WSGIMiddleware(landing_server))


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8050, reload=True)
