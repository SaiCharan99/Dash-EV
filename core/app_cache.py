from flask_caching import Cache

# Single cache instance shared across all Dash apps.
# Initialised with a Flask server in products/energy_dashboard/app.py via
# flask_cache.init_app(app.server, config={...})
flask_cache = Cache()
