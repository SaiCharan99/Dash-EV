import plotly.graph_objects as go
from dash import html, Input, Output

from core.design_tokens import (
    PANEL, TEXT, MUTED, SUBTLE, SEP, PALETTE,
    BLUE, GREEN, ORANGE, RED, PURPLE,
    ENERGY_SOURCE_COLORS, ENERGY_SOURCE_LABELS,
    ENERGY_COAL,
)
from core.chart_factory import _chart, _rgba
from core.layout_helpers import _legend_row
from core.app_cache import flask_cache


EMISSION_FACTORS = {
    'coal_black':          0.90,
    'coal_brown':          1.20,
    'gas_ccgt':            0.40,
    'gas_ocgt':            0.55,
    'gas_steam':           0.55,
    'gas_recip':           0.55,
    'distillate':          0.75,
    'solar_utility':       0.0,
    'solar_rooftop':       0.0,
    'wind':                0.0,
    'hydro':               0.0,
    'battery_discharging': 0.0,
    'bioenergy_biogas':    0.0,
    'bioenergy_biomass':   0.0,
}

COAL_RETIREMENT = [
    ('Hazelwood (VIC)',  1600, 1971, 2017),
    ('Liddell (NSW)',    2000, 1971, 2023),
    ('Eraring (NSW)',    2880, 1981, 2027),
    ('Yallourn (VIC)',   1480, 1973, 2028),
    ('Callide B (QLD)',   700, 1988, 2028),
    ('Bayswater (NSW)',  2640, 1985, 2033),
    ('Vales Point (NSW)',1320, 1978, 2033),
    ('Loy Yang A (VIC)', 2210, 1984, 2035),
    ('Tarong (QLD)',     1400, 1984, 2036),
    ('Loy Yang B (VIC)', 1070, 1993, 2046),
]


@flask_cache.memoize(timeout=300)
def _compute_generation(yr_range, regions, season):
    from products.energy_dashboard.data import filter_generation, NEM_REGIONS, FUEL_ORDER

    season_val = None if season == 'All' else season.lower()
    g = filter_generation(list(regions), list(yr_range), season=season_val)
    if g is None or g.empty:
        return None

    sources_present = [s for s in FUEL_ORDER if s in g.source.unique()]

    # ── Multi-line: annual GWh per source ────────────────────────────────────
    annual = g.groupby(['year', 'source'])['generation_gwh'].sum().reset_index()
    fig1 = go.Figure()
    for i, src in enumerate(sources_present):
        sub = annual[annual.source == src].sort_values('year')
        color = ENERGY_SOURCE_COLORS.get(src, PALETTE[i % len(PALETTE)])
        label = ENERGY_SOURCE_LABELS.get(src, src.replace('_', ' ').title())
        fig1.add_trace(go.Scatter(
            x=sub.year, y=sub.generation_gwh,
            name=label, mode='lines+markers',
            line=dict(color=color, width=2.5),
            marker=dict(size=6, color=PANEL, line=dict(color=color, width=2)),
            hovertemplate=f'<b>{label}</b>  %{{x}}: %{{y:,.0f}} GWh<extra></extra>',
        ))
    fig1.update_layout(**_chart(height=340))
    fig1.update_layout(yaxis_title='Generation (GWh)', hovermode='x unified')

    # ── Donut: latest year share ──────────────────────────────────────────────
    latest = g[g.year == g.year.max()]
    latest_src = latest.groupby('source')['generation_gwh'].sum().reset_index()
    latest_src = latest_src[latest_src.generation_gwh > 0]
    latest_src['label'] = latest_src.source.map(
        lambda s: ENERGY_SOURCE_LABELS.get(s, s.replace('_', ' ').title()))
    total_gen  = latest_src.generation_gwh.sum()
    fossil_pct = (latest_src[latest_src.source.isin(
        ['coal_black', 'coal_brown', 'gas_ccgt', 'gas_ocgt'])]['generation_gwh'].sum()
        / total_gen * 100) if total_gen else 0
    ren_pct = 100 - fossil_pct

    donut_colors = [ENERGY_SOURCE_COLORS.get(s, '#8E8E93') for s in latest_src.source]
    fig2 = go.Figure(go.Pie(
        labels=latest_src.label, values=latest_src.generation_gwh,
        hole=0.60,
        marker=dict(colors=donut_colors, line=dict(color=PANEL, width=3)),
        textinfo='none',
        hovertemplate='<b>%{label}</b>: %{value:,.0f} GWh (%{percent})<extra></extra>',
    ))
    fig2.update_layout(**_chart(height=240), showlegend=False)
    fig2.update_layout(
        margin=dict(l=20, r=20, t=20, b=4),
        annotations=[dict(
            text=f'<b>{ren_pct:.0f}%</b><br><span style="font-size:10px">renewable</span>',
            x=0.5, y=0.5, xref='paper', yref='paper',
            font=dict(size=17, color=TEXT, family='Inter'), showarrow=False, align='center',
        )],
    )
    legend_items = [
        (ENERGY_SOURCE_COLORS.get(row.source, '#8E8E93'),
         row.label,
         f'{row.generation_gwh:,.0f} GWh · {row.generation_gwh / total_gen * 100:.1f}%')
        for _, row in latest_src.iterrows()
    ]
    donut_legend = _legend_row(legend_items)

    # ── Stacked bar: annual GWh by fuel type ─────────────────────────────────
    fig3 = go.Figure()
    for src in sources_present:
        sub = annual[annual.source == src].sort_values('year')
        color = ENERGY_SOURCE_COLORS.get(src, '#8E8E93')
        label = ENERGY_SOURCE_LABELS.get(src, src.replace('_', ' ').title())
        fig3.add_trace(go.Bar(
            x=sub.year, y=sub.generation_gwh, name=label,
            marker=dict(color=color, line=dict(color='rgba(0,0,0,0)', width=0)),
            hovertemplate=f'<b>{label}</b>  %{{x}}: %{{y:,.0f}} GWh<extra></extra>',
        ))
    fig3.update_layout(**_chart(height=320), barmode='stack')
    fig3.update_layout(yaxis_title='Generation (GWh)', bargap=0.28)

    # ── Monthly stacked area: last 3 years ────────────────────────────────────
    last3 = g[g.year >= g.year.max() - 2].copy()
    last3['period'] = last3['year'].astype(str) + '-' + last3['month'].astype(str).str.zfill(2)
    monthly = last3.groupby(['period', 'source'])['generation_gwh'].sum().reset_index()
    fig4 = go.Figure()
    for src in sources_present:
        sub = monthly[monthly.source == src].sort_values('period')
        color = ENERGY_SOURCE_COLORS.get(src, '#8E8E93')
        label = ENERGY_SOURCE_LABELS.get(src, src.replace('_', ' ').title())
        fig4.add_trace(go.Scatter(
            x=sub.period, y=sub.generation_gwh,
            name=label, stackgroup='one', mode='lines',
            line=dict(color=color, width=1),
            hovertemplate=f'<b>{label}</b>  %{{x}}: %{{y:,.0f}} GWh<extra></extra>',
        ))
    fig4.update_layout(**_chart(height=320))
    fig4.update_layout(yaxis_title='Generation (GWh)', hovermode='x unified',
                       xaxis=dict(tickangle=-30, nticks=12))

    # ── Carbon intensity (tCO2/MWh) by year, per region ──────────────────────
    g_ann = g.groupby(['region', 'year', 'source'])['generation_gwh'].sum().reset_index()
    g_ann['emissions_tco2'] = g_ann.apply(
        lambda r: r.generation_gwh * 1000 * EMISSION_FACTORS.get(r.source, 0.0),
        axis=1,
    )
    em = g_ann.groupby(['region', 'year']).agg(
        total_gwh=('generation_gwh', 'sum'),
        total_em=('emissions_tco2',  'sum'),
    ).reset_index()
    em['intensity'] = em.total_em / (em.total_gwh * 1000)

    fig5 = go.Figure()
    for i, reg in enumerate(sorted(em.region.unique())):
        sub = em[em.region == reg].sort_values('year')
        fig5.add_trace(go.Scatter(
            x=sub.year, y=sub.intensity,
            name=reg, mode='lines+markers',
            line=dict(color=PALETTE[i], width=2.5),
            marker=dict(size=6, color=PANEL, line=dict(color=PALETTE[i], width=2)),
            hovertemplate=f'<b>{reg}</b>  %{{x}}: %{{y:.3f}} tCO₂/MWh<extra></extra>',
        ))
    nem_em = g_ann.groupby('year').agg(
        total_gwh=('generation_gwh', 'sum'),
        total_em=('emissions_tco2',  'sum'),
    ).reset_index()
    nem_em['intensity'] = nem_em.total_em / (nem_em.total_gwh * 1000)
    fig5.add_trace(go.Scatter(
        x=nem_em.year, y=nem_em.intensity,
        name='NEM avg', mode='lines',
        line=dict(color=TEXT, width=3, dash='dot'),
        hovertemplate='<b>NEM avg</b>  %{x}: %{y:.3f} tCO₂/MWh<extra></extra>',
    ))
    fig5.update_layout(**_chart(height=320))
    fig5.update_layout(yaxis_title='tCO₂ / MWh', hovermode='x unified')

    # ── Coal retirement runway (Gantt) ────────────────────────────────────────
    yr_now = 2026
    fig6 = go.Figure()
    sorted_units = sorted(COAL_RETIREMENT, key=lambda r: r[3])
    for i, (name, mw, start, end) in enumerate(sorted_units):
        retired = end < yr_now
        color = _rgba(ENERGY_COAL, 0.45) if retired else ENERGY_COAL
        fig6.add_trace(go.Bar(
            x=[end - start], y=[name], base=[start],
            orientation='h',
            marker=dict(color=color, line=dict(color='rgba(0,0,0,0)', width=0)),
            hovertemplate=(
                f'<b>{name}</b><br>'
                f'Capacity: {mw} MW<br>'
                f'Operating: {start} – {end}<extra></extra>'
            ),
            showlegend=False,
        ))
    fig6.add_vline(
        x=yr_now, line=dict(color=RED, width=1.5, dash='dash'),
        annotation_text='today', annotation_position='top',
        annotation_font=dict(color=RED, size=10),
    )
    fig6.update_layout(**_chart(height=320))
    fig6.update_layout(
        xaxis=dict(title='Year', range=[1965, 2050]),
        margin=dict(l=140, r=12, t=8, b=36),
        bargap=0.35,
    )

    return fig1, fig2, donut_legend, fig3, fig4, fig5, fig6


def register(app):
    @app.callback(
        Output('gen-trend-lines',     'figure'),
        Output('gen-donut',           'figure'),
        Output('gen-donut-legend',    'children'),
        Output('gen-stacked-bar',     'figure'),
        Output('gen-monthly-area',    'figure'),
        Output('gen-carbon-intensity','figure'),
        Output('gen-coal-runway',     'figure'),
        Input('en-yr-slider',     'value'),
        Input('en-region-filter', 'value'),
        Input('en-season-filter', 'value'),
    )
    def cb_generation(yr_range, regions, season):
        from api.cache import is_ready
        empty = go.Figure().update_layout(**_chart())
        if not is_ready():
            return empty, empty, [], empty, empty, empty, empty

        result = _compute_generation(
            tuple(yr_range),
            tuple(sorted(regions or [])),
            season or 'All',
        )
        if result is None:
            return empty, empty, [], empty, empty, empty, empty
        return result
