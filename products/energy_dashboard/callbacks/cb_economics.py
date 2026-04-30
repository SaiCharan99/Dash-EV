import plotly.graph_objects as go
from dash import Input, Output

from core.design_tokens import (
    PANEL, TEXT, MUTED,
    BLUE, GREEN, ORANGE, RED, PURPLE, TEAL,
    ENERGY_SOLAR, ENERGY_WIND, ENERGY_COAL, ENERGY_GAS,
)
from core.chart_factory import _chart, _rgba, _dual_axis_chart
from core.app_cache import flask_cache

TECH_COLORS = {
    'solar_utility': ENERGY_SOLAR,
    'wind_onshore':  ENERGY_WIND,
    'coal_black':    ENERGY_COAL,
    'gas_ccgt':      ENERGY_GAS,
    'gas_ocgt':      '#AEAEB2',
    'battery_2hr':   PURPLE,
}
TECH_LABELS = {
    'solar_utility': 'Solar Utility',
    'wind_onshore':  'Wind Onshore',
    'coal_black':    'Coal (Black)',
    'gas_ccgt':      'Gas CCGT',
    'gas_ocgt':      'Gas OCGT (Peaker)',
    'battery_2hr':   'Battery (2hr)',
}


@flask_cache.memoize(timeout=300)
def _compute_economics(yr_range, regions, season):
    from products.energy_dashboard.data import filter_demand, filter_prices, NEM_REGIONS
    from api.cache import get_lcoe_df

    lcoe  = get_lcoe_df()
    techs = list(TECH_COLORS.keys())

    # ── LCOE range bar ────────────────────────────────────────────────────────
    latest_lcoe = lcoe[lcoe.year == 2024]
    fig1 = go.Figure()
    for tech in techs:
        row = latest_lcoe[latest_lcoe.technology == tech]
        if row.empty:
            continue
        row = row.iloc[0]
        color = TECH_COLORS[tech]
        label = TECH_LABELS[tech]
        fig1.add_trace(go.Bar(
            x=[row.lcoe_high - row.lcoe_low], y=[label], orientation='h',
            base=[row.lcoe_low],
            marker=dict(color=_rgba(color, 0.65), line=dict(color=color, width=2)),
            hovertemplate=(
                f'<b>{label}</b><br>'
                f'Low: ${row.lcoe_low:.0f}  Mid: ${row.lcoe_mid:.0f}  High: ${row.lcoe_high:.0f}/MWh'
                '<extra></extra>'
            ),
            name=label, showlegend=False,
        ))
        fig1.add_trace(go.Scatter(
            x=[row.lcoe_mid], y=[label], mode='markers',
            marker=dict(color=color, size=10, symbol='diamond'),
            hovertemplate=f'Mid: ${row.lcoe_mid:.0f}/MWh<extra></extra>',
            showlegend=False,
        ))
    fig1.update_layout(**_chart(height=300), showlegend=False)
    fig1.update_layout(xaxis_title='LCOE ($/MWh)', margin=dict(l=140, r=12, t=8, b=36))

    # ── LCOE trend: cost trajectories 2015–2030 ───────────────────────────────
    fig2 = go.Figure()
    for tech in ['solar_utility', 'wind_onshore', 'coal_black', 'gas_ccgt', 'battery_2hr']:
        sub = lcoe[lcoe.technology == tech].sort_values('year')
        if sub.empty:
            continue
        color = TECH_COLORS[tech]
        label = TECH_LABELS[tech]
        actual = sub[~sub.is_projection]
        proj   = sub[sub.is_projection]
        if not actual.empty:
            fig2.add_trace(go.Scatter(
                x=actual.year, y=actual.lcoe_mid, name=label,
                mode='lines+markers', line=dict(color=color, width=2.5),
                marker=dict(size=6, color=PANEL, line=dict(color=color, width=2)),
                hovertemplate=f'<b>{label}</b>  %{{x}}: $%{{y:.0f}}/MWh<extra></extra>',
            ))
        if not proj.empty:
            fig2.add_trace(go.Scatter(
                x=proj.year, y=proj.lcoe_mid, name=f'{label} (proj.)',
                mode='lines', line=dict(color=color, width=1.5, dash='dot'),
                showlegend=False,
                hovertemplate=f'<b>{label} projected</b>  %{{x}}: $%{{y:.0f}}/MWh<extra></extra>',
            ))
    fig2.update_layout(**_chart(height=300))
    fig2.update_layout(yaxis_title='LCOE ($/MWh)')

    # ── Spot price vs LCOE ────────────────────────────────────────────────────
    p = filter_prices(list(regions), list(yr_range))
    fig3 = go.Figure()
    if p is not None and not p.empty:
        price_annual = p.groupby('year')['avg_spot_mwh'].mean().reset_index()
        fig3.add_trace(go.Scatter(
            x=price_annual.year, y=price_annual.avg_spot_mwh,
            name='Avg Spot Price', mode='lines+markers',
            line=dict(color=BLUE, width=2.5),
            marker=dict(size=7, color=PANEL, line=dict(color=BLUE, width=2)),
            hovertemplate='Spot price  %{x}: $%{y:.0f}/MWh<extra></extra>',
        ))
    for tech in ['solar_utility', 'wind_onshore']:
        sub = lcoe[(lcoe.technology == tech) & lcoe.year.between(*yr_range)]
        if sub.empty:
            continue
        color = TECH_COLORS[tech]
        label = TECH_LABELS[tech]
        fig3.add_trace(go.Scatter(
            x=sub.year, y=sub.lcoe_mid, name=f'{label} LCOE',
            mode='lines', line=dict(color=color, width=2, dash='dash'),
            hovertemplate=f'{label} LCOE  %{{x}}: $%{{y:.0f}}/MWh<extra></extra>',
        ))
        fig3.add_trace(go.Scatter(
            x=list(sub.year) + list(sub.year[::-1]),
            y=list(sub.lcoe_high) + list(sub.lcoe_low[::-1]),
            fill='toself', fillcolor=_rgba(color, 0.08),
            line=dict(color='rgba(0,0,0,0)'), showlegend=False, hoverinfo='skip',
        ))
    fig3.update_layout(**_chart(height=320))
    fig3.update_layout(yaxis_title='$/MWh', hovermode='x unified')

    # ── Demand vs avg cost (dual axis) ────────────────────────────────────────
    d = filter_demand(list(regions), list(yr_range), None)
    fig4 = go.Figure()
    if d is not None and not d.empty and p is not None and not p.empty:
        demand_annual = d.groupby('year')['demand_gwh'].sum().reset_index()
        demand_annual['twh'] = demand_annual.demand_gwh / 1000
        price_annual2 = p.groupby('year')['avg_spot_mwh'].mean().reset_index()
        fig4.add_trace(go.Bar(
            x=demand_annual.year, y=demand_annual.twh, name='Demand (TWh)',
            marker=dict(color=_rgba(BLUE, 0.55), line=dict(color='rgba(0,0,0,0)', width=0)),
            hovertemplate='%{x}: %{y:,.1f} TWh<extra></extra>', yaxis='y',
        ))
        fig4.add_trace(go.Scatter(
            x=price_annual2.year, y=price_annual2.avg_spot_mwh,
            name='Avg Price ($/MWh)', mode='lines+markers',
            line=dict(color=ORANGE, width=2.5),
            marker=dict(size=7, color=PANEL, line=dict(color=ORANGE, width=2)),
            hovertemplate='%{x}: $%{y:.0f}/MWh<extra></extra>', yaxis='y2',
        ))
    layout = _dual_axis_chart(height=320)
    layout['barmode'] = 'group'
    fig4.update_layout(**layout, bargap=0.32)
    fig4.update_layout(
        yaxis_title='Demand (TWh)',
        yaxis2_title='Avg Price ($/MWh)',
        hovermode='x unified',
    )

    return fig1, fig2, fig3, fig4


def register(app):
    @app.callback(
        Output('econ-lcoe-range',    'figure'),
        Output('econ-lcoe-trend',    'figure'),
        Output('econ-price-vs-lcoe', 'figure'),
        Output('econ-demand-cost',   'figure'),
        Input('en-yr-slider',     'value'),
        Input('en-region-filter', 'value'),
        Input('en-season-filter', 'value'),
    )
    def cb_economics(yr_range, regions, season):
        from api.cache import is_ready
        empty = go.Figure().update_layout(**_chart())
        if not is_ready():
            return empty, empty, empty, empty

        return _compute_economics(
            tuple(yr_range),
            tuple(sorted(regions or [])),
            season or 'All',
        )
