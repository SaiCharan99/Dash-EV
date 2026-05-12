import numpy as np
import plotly.graph_objects as go
from dash import Input, Output

from core.design_tokens import (
    PANEL, TEXT, MUTED, PALETTE,
    TEAL, ENERGY_SOLAR, ENERGY_WIND,
    ENERGY_SOURCE_COLORS, ENERGY_SOURCE_LABELS,
)
from core.chart_factory import _chart, _rgba
from core.app_cache import flask_cache


@flask_cache.memoize(timeout=300)
def _compute_renewables(yr_range, regions, season):
    from products.energy_dashboard.data import filter_generation, NEM_REGIONS
    import pandas as pd

    regions_list = list(regions)
    g = filter_generation(regions_list, list(yr_range))
    if g is None or g.empty:
        return None

    # ── Grouped bar: renewable % by state by year ─────────────────────────────
    annual       = g.groupby(['region', 'year', 'source_category'])['generation_gwh'].sum().reset_index()
    annual_total = annual.groupby(['region', 'year'])['generation_gwh'].sum().reset_index()
    annual_ren   = (annual[annual.source_category == 'renewable']
                   .groupby(['region', 'year'])['generation_gwh'].sum().reset_index())
    merged = annual_ren.merge(annual_total, on=['region', 'year'], suffixes=('_ren', '_tot'))
    merged['ren_pct'] = merged.generation_gwh_ren / merged.generation_gwh_tot * 100

    fig1 = go.Figure()
    for i, reg in enumerate(regions_list):
        sub = merged[merged.region == reg].sort_values('year')
        fig1.add_trace(go.Bar(
            x=sub.year, y=sub.ren_pct, name=reg,
            marker=dict(color=PALETTE[i], opacity=0.82,
                        line=dict(color='rgba(0,0,0,0)', width=0)),
            hovertemplate=f'<b>{reg}</b>  %{{x}}: %{{y:.1f}}%<extra></extra>',
        ))
    fig1.update_layout(**_chart(height=320), barmode='group', bargap=0.18)
    fig1.update_layout(yaxis_title='Renewable Share (%)')

    # ── Heatmap: capacity factor by month × region ────────────────────────────
    empty_fig = go.Figure().update_layout(**_chart())
    g_cf = g[g.source.isin(['solar_utility', 'wind']) & g.capacity_factor.notna()]
    if not g_cf.empty:
        cf_agg = g_cf.groupby(['region', 'month'])['capacity_factor'].mean().reset_index()
        pivot  = cf_agg.pivot(index='region', columns='month', values='capacity_factor').fillna(0)
        month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        fig2 = go.Figure(go.Heatmap(
            z=pivot.values * 100,
            x=[month_names[m - 1] for m in pivot.columns],
            y=pivot.index,
            colorscale=[[0, '#EBF3FF'], [0.5, TEAL],
                        [1, ENERGY_SOURCE_COLORS['solar_utility']]],
            hovertemplate='%{y} %{x}: <b>%{z:.1f}%</b> CF<extra></extra>',
            colorbar=dict(
                title=dict(text='CF %', font=dict(color=MUTED, size=11)),
                tickfont=dict(color=MUTED, size=11),
                bgcolor='rgba(0,0,0,0)', thickness=10, len=0.7,
                outlinecolor='rgba(0,0,0,0)',
            ),
        ))
        fig2.update_layout(**_chart(height=280))
        fig2.update_layout(margin=dict(l=48, r=80, t=16, b=40))
    else:
        fig2 = empty_fig

    # ── Waterfall: net GWh change since earliest year ─────────────────────────
    yr0   = g.year.min()
    yr1   = g.year.max()
    base  = g[g.year == yr0].groupby('source')['generation_gwh'].sum()
    curr  = g[g.year == yr1].groupby('source')['generation_gwh'].sum()
    delta = (curr - base).dropna().sort_values()
    sources   = delta.index.tolist()
    values    = delta.values.tolist()
    colors    = [ENERGY_SOURCE_COLORS.get(s, '#8E8E93') for s in sources]
    bar_colors = [_rgba(c, 0.55 if v < 0 else 0.85) for c, v in zip(colors, values)]
    labels    = [ENERGY_SOURCE_LABELS.get(s, s.replace('_', ' ').title()) for s in sources]

    fig3 = go.Figure(go.Bar(
        x=values, y=labels, orientation='h',
        marker=dict(color=bar_colors, line=dict(color='rgba(0,0,0,0)', width=0)),
        hovertemplate='<b>%{y}</b>: %{x:+,.0f} GWh<extra></extra>',
    ))
    fig3.add_vline(x=0, line=dict(color=TEXT, width=1))
    fig3.update_layout(**_chart(height=320), showlegend=False)
    fig3.update_layout(
        xaxis_title=f'Net GWh change  {yr0}→{yr1}',
        margin=dict(l=140, r=12, t=8, b=36),
    )

    # ── Solar–Wind complementarity scatter (monthly GWh) ──────────────────────
    monthly = g.groupby(['region', 'year', 'month', 'source'])['generation_gwh'].sum().reset_index()
    pivot = monthly.pivot_table(
        index=['region', 'year', 'month'],
        columns='source',
        values='generation_gwh',
        aggfunc='sum',
    ).reset_index().fillna(0)

    solar_cols = [c for c in pivot.columns if c in ('solar_utility', 'solar_rooftop')]
    wind_cols  = [c for c in pivot.columns if c == 'wind']

    fig4 = go.Figure()
    if solar_cols and wind_cols:
        pivot['solar_total'] = pivot[solar_cols].sum(axis=1)
        pivot['wind_total']  = pivot[wind_cols].sum(axis=1)
        valid = pivot[(pivot.solar_total > 0) & (pivot.wind_total > 0)]
        if not valid.empty:
            for i, reg in enumerate(sorted(valid.region.unique())):
                sub = valid[valid.region == reg]
                color = PALETTE[i % len(PALETTE)]
                fig4.add_trace(go.Scatter(
                    x=sub.solar_total, y=sub.wind_total,
                    mode='markers', name=reg,
                    marker=dict(size=7, color=_rgba(color, 0.55),
                                line=dict(color=color, width=1)),
                    customdata=np.column_stack([sub.year, sub.month]),
                    hovertemplate=(
                        f'<b>{reg}</b> %{{customdata[0]}}-%{{customdata[1]:02d}}<br>'
                        'Solar: %{x:,.0f} GWh<br>'
                        'Wind:  %{y:,.0f} GWh<extra></extra>'
                    ),
                ))
            if len(valid) > 2:
                corr = float(np.corrcoef(valid.solar_total, valid.wind_total)[0, 1])
                slope, intercept = np.polyfit(valid.solar_total, valid.wind_total, 1)
                x_line = np.array([valid.solar_total.min(), valid.solar_total.max()])
                fig4.add_trace(go.Scatter(
                    x=x_line, y=slope * x_line + intercept,
                    mode='lines', name=f'trend (r={corr:.2f})',
                    line=dict(color=TEXT, width=1.5, dash='dash'),
                    hoverinfo='skip',
                ))
    fig4.update_layout(**_chart(height=320))
    fig4.update_layout(
        xaxis_title='Solar GWh (monthly)',
        yaxis_title='Wind GWh (monthly)',
    )

    return fig1, fig2, fig3, fig4


def register(app):
    @app.callback(
        Output('ren-share-bar',         'figure'),
        Output('ren-cf-heatmap',        'figure'),
        Output('ren-growth-waterfall',  'figure'),
        Output('ren-solar-wind-corr',   'figure'),
        Input('en-yr-slider',     'value'),
        Input('en-region-filter', 'value'),
        Input('en-season-filter', 'value'),
    )
    def cb_renewables(yr_range, regions, season):
        from api.cache import is_ready
        empty = go.Figure().update_layout(**_chart())
        if not is_ready():
            return empty, empty, empty, empty

        result = _compute_renewables(
            tuple(yr_range),
            tuple(sorted(regions or [])),
            season or 'All',
        )
        if result is None:
            return empty, empty, empty, empty
        return result
