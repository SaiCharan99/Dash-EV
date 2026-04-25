import plotly.graph_objects as go
from dash import html, Input, Output

from core.design_tokens import (
    PANEL, TEXT, MUTED, SUBTLE, PALETTE,
    ENERGY_SOURCE_COLORS, ENERGY_SOURCE_LABELS,
)
from core.chart_factory import _chart
from core.layout_helpers import _legend_row


def register(app):
    @app.callback(
        Output('gen-trend-lines',  'figure'),
        Output('gen-donut',        'figure'),
        Output('gen-donut-legend', 'children'),
        Output('gen-stacked-bar',  'figure'),
        Output('gen-monthly-area', 'figure'),
        Input('en-yr-slider',     'value'),
        Input('en-region-filter', 'value'),
        Input('en-season-filter', 'value'),
    )
    def cb_generation(yr_range, regions, season):
        from products.energy_dashboard.data import (
            filter_generation, NEM_REGIONS, FUEL_ORDER,
        )
        from api.cache import is_ready

        empty = go.Figure().update_layout(**_chart())
        if not is_ready():
            return empty, empty, [], empty, empty

        season_val = None if season == 'All' else season.lower()
        g = filter_generation(regions or NEM_REGIONS, yr_range, season=season_val)
        if g is None or g.empty:
            return empty, empty, [], empty, empty

        sources_present = [s for s in FUEL_ORDER if s in g.source.unique()]
        colors = [ENERGY_SOURCE_COLORS.get(s, '#8E8E93') for s in sources_present]

        # ── Multi-line: annual GWh per source (fossil ↓ vs renewable ↑) ───────
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

        # ── Donut: latest year share ──────────────────────────────────────────
        latest = g[g.year == g.year.max()]
        latest_src = latest.groupby('source')['generation_gwh'].sum().reset_index()
        latest_src = latest_src[latest_src.generation_gwh > 0]
        latest_src['label'] = latest_src.source.map(
            lambda s: ENERGY_SOURCE_LABELS.get(s, s.replace('_', ' ').title()))
        total_gen = latest_src.generation_gwh.sum()
        fossil_pct = (latest_src[latest_src.source.isin(
            ['coal_black','coal_brown','gas_ccgt','gas_ocgt'])]['generation_gwh'].sum()
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
                font=dict(size=17, color=TEXT, family='Inter'), showarrow=False,
                align='center',
            )],
        )
        legend_items = [
            (ENERGY_SOURCE_COLORS.get(row.source, '#8E8E93'),
             row.label,
             f'{row.generation_gwh:,.0f} GWh · {row.generation_gwh/total_gen*100:.1f}%')
            for _, row in latest_src.iterrows()
        ]
        donut_legend = _legend_row(legend_items)

        # ── Stacked bar: annual GWh by fuel type ─────────────────────────────
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

        # ── Monthly stacked area: last 3 years ────────────────────────────────
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

        return fig1, fig2, donut_legend, fig3, fig4
