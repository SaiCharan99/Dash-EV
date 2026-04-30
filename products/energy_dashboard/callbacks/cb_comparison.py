import numpy as np
import plotly.graph_objects as go
from dash import Input, Output

from core.design_tokens import (
    PANEL, TEXT, MUTED, BG, BG2, SEP,
    BLUE, GREEN, ORANGE, PURPLE, TEAL, PALETTE,
    ENERGY_SOURCE_COLORS, ENERGY_SOURCE_LABELS,
)
from core.chart_factory import _chart, _rgba
from core.app_cache import flask_cache


@flask_cache.memoize(timeout=300)
def _compute_comparison(yr_range, regions, season):
    from products.energy_dashboard.data import (
        filter_demand, filter_generation, filter_prices,
        NEM_REGIONS, REGION_COORDS, REGION_LABELS, FUEL_ORDER,
    )

    all_regions = list(regions) or NEM_REGIONS
    yr0, yr1    = yr_range
    latest_year = yr1

    g = filter_generation(all_regions, [latest_year, latest_year])
    d = filter_demand(all_regions, list(yr_range), None)
    p = filter_prices(all_regions, list(yr_range))

    # ── Grouped bar: GWh by source per state ─────────────────────────────
    fig1 = go.Figure()
    if g is not None and not g.empty:
        sources_present = [s for s in FUEL_ORDER if s in g.source.unique()]
        for src in sources_present:
            sub   = g[g.source == src].groupby('region')['generation_gwh'].sum().reset_index()
            color = ENERGY_SOURCE_COLORS.get(src, '#8E8E93')
            label = ENERGY_SOURCE_LABELS.get(src, src.replace('_', ' ').title())
            fig1.add_trace(go.Bar(
                x=sub.region, y=sub.generation_gwh, name=label,
                marker=dict(color=color, line=dict(color='rgba(0,0,0,0)', width=0)),
                hovertemplate=f'<b>%{{x}}</b> {label}: %{{y:,.0f}} GWh<extra></extra>',
            ))
    fig1.update_layout(**_chart(height=340), barmode='group', bargap=0.2)
    fig1.update_layout(yaxis_title='Generation (GWh)')

    # ── Radar: 5 axes per state ───────────────────────────────────────────
    axes = ['Renewable %', 'Avg Price', 'Peak Demand', 'Solar CF', 'Wind CF']
    fig2 = go.Figure()
    for i, reg in enumerate(all_regions):
        g_reg = g[g.region == reg] if g is not None and not g.empty else None
        d_reg = d[d.region == reg] if d is not None and not d.empty else None
        p_reg = p[p.region == reg] if p is not None and not p.empty else None

        if g_reg is not None and not g_reg.empty:
            tot     = g_reg['generation_gwh'].sum()
            ren     = g_reg[g_reg.source_category == 'renewable']['generation_gwh'].sum()
            ren_pct = ren / tot * 100 if tot else 0
            solar_cf = float(g_reg[g_reg.source == 'solar_utility']['capacity_factor'].mean()
                             if 'capacity_factor' in g_reg.columns else 0) or 0
            wind_cf  = float(g_reg[g_reg.source == 'wind']['capacity_factor'].mean()
                             if 'capacity_factor' in g_reg.columns else 0) or 0
        else:
            ren_pct = solar_cf = wind_cf = 0

        avg_price = float(p_reg['avg_spot_mwh'].mean()) if p_reg is not None and not p_reg.empty else 0
        peak_gw   = float(d_reg['peak_demand_gw'].max()) if d_reg is not None and not d_reg.empty else 0

        vals = [
            min(ren_pct, 100),
            min(avg_price / 2, 100),
            min(peak_gw * 10, 100),
            min(solar_cf * 100, 100),
            min(wind_cf * 100, 100),
        ]
        vals.append(vals[0])

        fig2.add_trace(go.Scatterpolar(
            r=vals, theta=axes + [axes[0]],
            name=reg, fill='toself',
            line=dict(color=PALETTE[i], width=2),
            fillcolor=_rgba(PALETTE[i], 0.1),
            hovertemplate=f'<b>{reg}</b><br>%{{theta}}: %{{r:.1f}}<extra></extra>',
        ))
    fig2.update_layout(**_chart(height=340))
    fig2.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont=dict(color=MUTED, size=10),
                            gridcolor='#EBEBF0'),
            angularaxis=dict(tickfont=dict(color=TEXT, size=12)),
            bgcolor=PANEL,
        ),
    )

    # ── Scattergeo: Australia map ─────────────────────────────────────────
    demand_by_region = {}
    price_by_region  = {}
    if d is not None and not d.empty:
        demand_by_region = d.groupby('region')['demand_gwh'].sum().to_dict()
    if p is not None and not p.empty:
        price_by_region  = p.groupby('region')['avg_spot_mwh'].mean().to_dict()

    lats    = [REGION_COORDS.get(r, (0, 0))[0] for r in all_regions]
    lons    = [REGION_COORDS.get(r, (0, 0))[1] for r in all_regions]
    demands = [demand_by_region.get(r, 0) for r in all_regions]
    prices  = [price_by_region.get(r, 0)  for r in all_regions]
    max_d   = max(demands) if demands else 1

    fig3 = go.Figure(go.Scattergeo(
        lat=lats, lon=lons,
        text=[REGION_LABELS.get(r, r) for r in all_regions],
        customdata=list(zip(demands, prices, all_regions)),
        mode='markers+text', textfont=dict(size=11, color=TEXT),
        textposition='top center',
        marker=dict(
            size=[np.sqrt(d / max_d) * 50 + 10 for d in demands],
            color=prices,
            colorscale=[[0, _rgba(GREEN, 0.7)], [0.5, ORANGE], [1, '#FF3B30']],
            opacity=0.85, line=dict(color=PANEL, width=2),
            showscale=True,
            colorbar=dict(
                title=dict(text='$/MWh', font=dict(color=MUTED, size=11)),
                tickfont=dict(color=MUTED, size=11),
                bgcolor='rgba(0,0,0,0)', thickness=10, len=0.6,
                outlinecolor='rgba(0,0,0,0)',
            ),
        ),
        hovertemplate=(
            '<b>%{customdata[2]}</b><br>'
            'Total Demand: %{customdata[0]:,.0f} GWh<br>'
            'Avg Price: $%{customdata[1]:.0f}/MWh'
            '<extra></extra>'
        ),
    ))
    fig3.update_layout(**_chart(height=420))
    fig3.update_layout(
        paper_bgcolor=PANEL,
        geo=dict(
            bgcolor=BG, showframe=False,
            showcoastlines=True, coastlinecolor=SEP,
            showland=True, landcolor='#EDE8F8',
            showocean=True, oceancolor=BG2,
            lonaxis=dict(range=[112, 155]),
            lataxis=dict(range=[-44, -10]),
            projection_type='mercator',
        ),
        margin=dict(l=0, r=0, t=8, b=0),
    )

    return fig1, fig2, fig3


def register(app):
    @app.callback(
        Output('sc-grouped-bar', 'figure'),
        Output('sc-radar',       'figure'),
        Output('sc-price-map',   'figure'),
        Input('en-yr-slider',     'value'),
        Input('en-region-filter', 'value'),
        Input('en-season-filter', 'value'),
    )
    def cb_comparison(yr_range, regions, season):
        from api.cache import is_ready
        empty = go.Figure().update_layout(**_chart())
        if not is_ready():
            return empty, empty, empty

        return _compute_comparison(
            tuple(yr_range),
            tuple(sorted(regions or [])),
            season or 'All',
        )
