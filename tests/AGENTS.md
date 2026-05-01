# tests/ — Test Suite

Three layers with different data requirements and speed profiles.

## Layers

| Layer | Path | Count | Data needed | Speed |
|-------|------|-------|-------------|-------|
| Unit | `tests/unit/` | ~175 tests | None (synthetic fixtures) | Fast |
| Integration | `tests/integration/` | ~46 tests | Real parquet files | Medium |
| E2E | `tests/e2e/` | ~32 tests | None | Slow (app startup) |

## Run commands

```bash
pytest tests/unit/                  # fast, no setup needed
pytest tests/integration/           # requires data/energy/*.parquet
pytest tests/e2e/                   # requires app to be importable
pytest                              # all layers
pytest -x                           # stop on first failure
pytest tests/unit/test_figures.py   # single file
```

Integration tests **auto-skip** if parquet files are absent — they do not fail.

## conftest.py — shared fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `demand_df` | session | Synthetic demand DataFrame (all 5 regions, 2015–2024) |
| `generation_df` | session | Synthetic generation DataFrame (5 sources) |
| `prices_df` | session | Synthetic prices DataFrame |
| `lcoe_df` | session | Synthetic LCOE DataFrame |
| `patched_cache` | function | Injects synthetic DFs into `api.cache` via monkeypatch — no disk I/O |
| `real_cache` | session | Loads real parquet files; skips if missing |
| `api_client` | session | FastAPI `TestClient` with real data loaded |
| `api_client_no_data` | session | FastAPI `TestClient` with cache cleared (tests 503 responses) |

## Key rule

Unit tests use `patched_cache` (synthetic data, no files). Integration tests use `real_cache` / `api_client` (real parquet files). Never mix — `patched_cache` and `real_cache` are mutually exclusive in a test.
