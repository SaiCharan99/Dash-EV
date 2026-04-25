from dash import html, Input, Output
from core.design_tokens import GREEN, BLUE, TEAL, ORANGE, PURPLE, MUTED, RED, TEXT


def register(app):
    @app.callback(
        Output('en-kpi-total', 'children'),
        Output('en-kpi-peak',  'children'),
        Output('en-kpi-renew', 'children'),
        Output('en-kpi-price', 'children'),
        Output('en-kpi-yoy',   'children'),
        Input('en-yr-slider',     'value'),
        Input('en-region-filter', 'value'),
        Input('en-season-filter', 'value'),
    )
    def cb_kpis(yr_range, regions, season):
        from products.energy_dashboard.data import filter_demand, filter_generation, filter_prices
        from api.cache import is_ready

        def _tile(label, value, sub, accent):
            return html.Div([
                html.Div(label, style={
                    'fontSize': '11px', 'fontWeight': '600', 'color': '#8E8E93',
                    'textTransform': 'uppercase', 'letterSpacing': '0.8px',
                }),
                html.Div(value, style={
                    'fontSize': '2rem', 'fontWeight': '700', 'color': TEXT,
                    'letterSpacing': '-0.8px', 'lineHeight': '1.1', 'marginTop': '10px',
                    'fontVariantNumeric': 'tabular-nums',
                }),
                html.Div(sub, style={
                    'fontSize': '12px', 'color': MUTED, 'marginTop': '6px',
                }),
            ])

        if not is_ready():
            empty = _tile('—', '—', 'No data loaded', BLUE)
            return empty, empty, empty, empty, empty

        yr0, yr1 = yr_range
        d  = filter_demand(regions, yr_range, season if season != 'All' else None)
        g  = filter_generation(regions, yr_range, season=season if season != 'All' else None)
        p  = filter_prices(regions, yr_range)
        dp = filter_demand(regions, [yr0, max(yr0, yr1 - 1)], None)

        total_twh = d['demand_gwh'].sum() / 1000 if d is not None and len(d) else 0
        peak_gw   = d['peak_demand_gw'].max() if d is not None and len(d) else 0

        ren_gwh   = g[g.source_category == 'renewable']['generation_gwh'].sum() if g is not None and len(g) else 0
        tot_gwh   = g['generation_gwh'].sum() if g is not None and len(g) else 0
        ren_pct   = ren_gwh / tot_gwh * 100 if tot_gwh else 0

        avg_price = p['avg_spot_mwh'].mean() if p is not None and len(p) else 0

        prev_twh  = dp['demand_gwh'].sum() / 1000 if dp is not None and len(dp) else total_twh
        yoy_pct   = (total_twh - prev_twh) / prev_twh * 100 if prev_twh else 0
        yoy_col   = {'color': GREEN if yoy_pct >= 0 else RED, 'fontSize': '12px'}

        return (
            _tile('Total Demand', f'{total_twh:,.0f} TWh', f'{yr0}–{yr1}', GREEN),
            _tile('Peak Demand',  f'{peak_gw:.1f} GW', 'max monthly', BLUE),
            _tile('Renewable Share', f'{ren_pct:.1f}%', 'of generation', TEAL),
            _tile('Avg Spot Price', f'${avg_price:.0f}/MWh', 'volume-weighted avg', ORANGE),
            _tile('YoY Change',
                  html.Span(('↑ ' if yoy_pct >= 0 else '↓ ') + f'{abs(yoy_pct):.1f}%',
                             style=yoy_col),
                  'demand vs prior year', PURPLE),
        )
