import numpy as np
import plotly.graph_objects as go
from dash import Input, Output

from core.design_tokens import PANEL, TEXT, MUTED, SUBTLE, SEP, PALETTE, ORANGE
from core.chart_factory import _chart


def register(app):
    @app.callback(
        Output('dem-timeseries',   'figure'),
        Output('dem-seasonal-box', 'figure'),
        Output('dem-heatmap',      'figure'),
        Input('en-yr-slider',     'value'),
        Input('en-region-filter', 'value'),
        Input('en-season-filter', 'value'),
    )
    def cb_demand(yr_range, regions, season):
        from products.energy_dashboard.data import filter_demand, NEM_REGIONS
        from api.cache import is_ready

        empty = go.Figure().update_layout(**_chart(), title='No data — run data pipeline')

        if not is_ready():
            return empty, empty, empty

        d = filter_demand(regions or NEM_REGIONS, yr_range, None)
        if d is None or d.empty:
            return empty, empty, empty

        # ── Stacked area: monthly GWh by region ──────────────────────────────
        d_monthly = d.copy()
        d_monthly['period'] = d_monthly['year'].astype(str) + '-' + d_monthly['month'].astype(str).str.zfill(2)
        fig1 = go.Figure()
        for i, reg in enumerate(regions or NEM_REGIONS):
            sub = d_monthly[d_monthly.region == reg].sort_values('period')
            if sub.empty:
                continue
            fig1.add_trace(go.Scatter(
                x=sub.period, y=sub.demand_gwh,
                name=reg, stackgroup='one', mode='lines',
                line=dict(color=PALETTE[i], width=1),
                hovertemplate=f'<b>{reg}</b>  %{{x}}: %{{y:,.0f}} GWh<extra></extra>',
            ))
        fig1.update_layout(**_chart(height=320))
        fig1.update_layout(yaxis_title='Demand (GWh)', hovermode='x unified',
                           xaxis=dict(tickangle=-30, nticks=12))

        # ── Box plot: seasonal distribution ───────────────────────────────────
        season_filter = None if season == 'All' else season.lower()
        d_box = filter_demand(regions or NEM_REGIONS, yr_range, season_filter)
        if d_box is None:
            d_box = d
        fig2 = go.Figure()
        for i, s in enumerate(['summer', 'autumn', 'winter', 'spring']):
            sub = d_box[d_box.season == s]
            fig2.add_trace(go.Box(
                y=sub.demand_gwh, name=s.capitalize(),
                marker_color=PALETTE[i], line_color=PALETTE[i],
                boxpoints='outliers', jitter=0.3, pointpos=-1.5,
                hovertemplate=f'<b>{s.capitalize()}</b>: %{{y:,.0f}} GWh<extra></extra>',
            ))
        fig2.update_layout(**_chart(height=320), showlegend=False)
        fig2.update_layout(yaxis_title='Demand (GWh)')

        # ── Heatmap: avg daily GW · month × year ─────────────────────────────
        d_heat = d.groupby(['year', 'month'])['demand_gwh'].mean().reset_index()
        import calendar
        d_heat['daily_gw'] = d_heat.apply(
            lambda r: r.demand_gwh / (calendar.monthrange(int(r.year), int(r.month))[1] * 24), axis=1
        )
        pivot = d_heat.pivot(index='year', columns='month', values='daily_gw')
        month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        fig3 = go.Figure(go.Heatmap(
            z=pivot.values,
            x=[month_names[m-1] for m in pivot.columns],
            y=pivot.index.astype(str),
            colorscale=[[0, '#EBF3FF'], [0.5, '#007AFF'], [1, '#AF52DE']],
            hovertemplate='%{y} %{x}: <b>%{z:.2f} GW</b><extra></extra>',
            colorbar=dict(
                title=dict(text='Avg GW', font=dict(color=MUTED, size=11)),
                tickfont=dict(color=MUTED, size=11),
                bgcolor='rgba(0,0,0,0)', thickness=10, len=0.7,
                outlinecolor='rgba(0,0,0,0)',
            ),
        ))
        fig3.update_layout(**_chart(height=320))
        fig3.update_layout(
            xaxis=dict(side='bottom'),
            margin=dict(l=48, r=80, t=16, b=40),
        )

        return fig1, fig2, fig3
