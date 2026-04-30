import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import numpy as np

from core.design_tokens import (
    BG, BG2, PANEL, TEXT, SECONDARY, MUTED, SUBTLE, SEP,
    BLUE, GREEN, ORANGE, RED, PURPLE, TEAL, PALETTE,
    NAV_BG, NAV_TEXT, NAV_MUTE,
    CARD_BORDER, CARD_SHADOW,
)
from core.chart_factory import _chart, _rgba, _bar_h
from core.layout_helpers import _panel, _ph, _row, _kpi, _legend_row, _pill_label
from products.ev_dashboard.data import (
    DF, ALL_MAKES, YEARS_WA, WA_COUNTIES,
    df_battery, df_global,
    _filter,
)

app = dash.Dash(
    __name__,
    requests_pathname_prefix='/ev/',
    assets_folder='../../assets',
    suppress_callback_exceptions=True,
    title='EV Dashboard',
)
server = app.server

_yr_marks = {
    y: {'label': str(y), 'style': {'color': SUBTLE, 'fontSize': '10px'}}
    for y in YEARS_WA if y % 2 == 1
}

def _ts():
    return {
        'background': 'transparent', 'border': 'none',
        'borderBottom': '2.5px solid transparent',
        'color': NAV_MUTE, 'fontSize': '13px', 'fontWeight': '500',
        'padding': '14px 16px', 'fontFamily': 'Inter, sans-serif',
        'letterSpacing': '-0.1px',
    }

def _tss():
    s = _ts()
    s.update({'color': NAV_TEXT, 'fontWeight': '600', 'borderBottom': f'2.5px solid {BLUE}'})
    return s


app.layout = html.Div([

    # ── nav ───────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Span('EV', style={
                'fontWeight': '700', 'color': NAV_TEXT, 'fontSize': '14px',
                'letterSpacing': '-0.3px',
            }),
            html.Span('  Market Intelligence', style={
                'fontWeight': '400', 'color': NAV_MUTE, 'fontSize': '14px',
            }),
        ], style={'whiteSpace': 'nowrap'}),

        html.Div([
            dcc.Tabs(id='main-tabs', value='overview', children=[
                dcc.Tab(label='Fleet Overview', value='overview', style=_ts(), selected_style=_tss()),
                dcc.Tab(label='Manufacturers',  value='mfr',      style=_ts(), selected_style=_tss()),
                dcc.Tab(label='Models & Range', value='models',   style=_ts(), selected_style=_tss()),
                dcc.Tab(label='Geography',      value='geo',      style=_ts(), selected_style=_tss()),
                dcc.Tab(label='Global Context', value='global',   style=_ts(), selected_style=_tss()),
            ], colors={'border': 'transparent', 'primary': BLUE, 'background': 'transparent'},
               style={'border': 'none'}),
        ], style={'flex': '1', 'display': 'flex', 'justifyContent': 'center'}),

        html.A('← Home', href='/', style={
            'fontSize': '12px', 'color': NAV_MUTE, 'textDecoration': 'none',
            'whiteSpace': 'nowrap', 'letterSpacing': '0.1px',
        }),
    ], style={
        'background': 'rgba(28,28,30,0.88)',
        'backdropFilter': 'blur(20px) saturate(180%)',
        'WebkitBackdropFilter': 'blur(20px) saturate(180%)',
        'padding': '0 32px',
        'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between',
        'position': 'sticky', 'top': '0', 'zIndex': '100', 'minHeight': '56px',
        'borderBottom': '1px solid rgba(255,255,255,0.06)',
    }),

    html.Div([

        # ── page header ───────────────────────────────────────────────
        html.Div([
            html.Div([
                html.H1('EV Market Intelligence', style={
                    'fontSize': '32px', 'fontWeight': '800', 'color': TEXT,
                    'letterSpacing': '-0.8px', 'margin': '0', 'lineHeight': '1.1',
                }),
                html.P('Washington State Department of Licensing · 280,000+ registered vehicles',
                       style={'fontSize': '13px', 'color': MUTED, 'marginTop': '7px',
                              'fontWeight': '400'}),
            ]),
        ], style={'padding': '36px 36px 0'}),

        # ── filter bar ────────────────────────────────────────────────
        html.Div([
            html.Div([
                _pill_label('Model Year'),
                dcc.RangeSlider(
                    id='yr-slider', min=2015, max=2025, step=1, value=[2015, 2025],
                    marks=_yr_marks, allowCross=False,
                    tooltip={'placement': 'bottom', 'always_visible': False},
                ),
            ], style={'flex': '3', 'minWidth': '240px'}),

            html.Div(style={'width': '1px', 'background': SEP, 'alignSelf': 'stretch'}),

            html.Div([
                _pill_label('EV Type'),
                dcc.RadioItems(
                    id='type-filter', value='All', inline=True,
                    options=[{'label': 'All', 'value': 'All'},
                             {'label': 'BEV', 'value': 'BEV'},
                             {'label': 'PHEV', 'value': 'PHEV'}],
                    className='seg-control',
                    inputStyle={}, labelStyle={},
                ),
            ], style={'flex': '1'}),

            html.Div(style={'width': '1px', 'background': SEP, 'alignSelf': 'stretch'}),

            html.Div([
                _pill_label('Make'),
                dcc.Dropdown(
                    id='make-filter',
                    options=[{'label': m, 'value': m} for m in ALL_MAKES],
                    value='All', clearable=False, style={'minWidth': '160px'},
                ),
            ], style={'flex': '1.2'}),
        ], style={
            'display': 'flex', 'alignItems': 'center', 'gap': '28px',
            'background': PANEL,
            'borderRadius': '18px',
            'border': f'1px solid {CARD_BORDER}',
            'boxShadow': CARD_SHADOW,
            'padding': '18px 28px',
            'margin': '24px 36px 0',
            'flexWrap': 'wrap',
        }, className='filter-bar'),

        # ── KPI strip ─────────────────────────────────────────────────
        html.Div([
            _kpi('Total EVs',              'kpi-total', 'kpi-total-d', BLUE),
            _kpi('Battery Electric (BEV)', 'kpi-bev',   'kpi-bev-d',   GREEN),
            _kpi('Plug-in Hybrid (PHEV)',  'kpi-phev',  'kpi-phev-d',  ORANGE),
            _kpi('Market Leader',          'kpi-top',   'kpi-top-d',   PURPLE),
        ], style={'display': 'flex', 'gap': '16px', 'padding': '20px 36px 0', 'flexWrap': 'wrap'}),

        html.Div(id='tab-content'),

    ], style={'background': BG, 'minHeight': 'calc(100vh - 56px)'}),

    # ── footer ────────────────────────────────────────────────────────
    html.Div([
        html.Div(
            'Washington State DOL  ·  IEA Global EV Outlook  ·  BloombergNEF  ·  Dash & Plotly',
            style={'color': SUBTLE, 'fontSize': '11px'},
        ),
    ], style={
        'textAlign': 'center', 'padding': '20px',
        'background': PANEL, 'borderTop': f'1px solid {SEP}',
    }),

], style={'fontFamily': 'Inter, -apple-system, sans-serif'})


@app.callback(Output('tab-content', 'children'), Input('main-tabs', 'value'))
def render_tab(tab):
    P = '24px 36px 36px'

    if tab == 'overview':
        return html.Div([
            _row(
                _panel([
                    _ph('Registrations by Model Year', 'Annual growth · BEV vs PHEV'),
                    html.Div(style={'height': '16px'}),
                    dcc.Graph(id='ov-year-bar', config={'displayModeBar': False}),
                ], flex=2),
                _panel([
                    _ph('BEV vs PHEV Split', 'Share of registered EVs'),
                    dcc.Graph(id='ov-type-pie', config={'displayModeBar': False}),
                    html.Div(id='ov-type-legend'),
                ]),
            ),
            _row(
                _panel([
                    _ph('Top 15 Makes', 'By total registered vehicles'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='ov-make-bar', config={'displayModeBar': False}),
                ]),
                _panel([
                    _ph('Top 15 Models', 'Most popular EV models in WA'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='ov-model-bar', config={'displayModeBar': False}),
                ]),
            ),
        ], style={'padding': P})

    if tab == 'mfr':
        return html.Div([
            _row(
                _panel([
                    _ph('Market Share', 'Top 10 manufacturers + others'),
                    dcc.Graph(id='mf-pie', config={'displayModeBar': False}),
                    html.Div(id='mf-pie-legend'),
                ], flex='1.1'),
                _panel([
                    _ph('BEV vs PHEV by Make', 'Top 12 manufacturers'),
                    html.Div(style={'height': '16px'}),
                    dcc.Graph(id='mf-type-bar', config={'displayModeBar': False}),
                ], flex=2),
            ),
            _row(
                _panel([
                    _ph('Registration Trend by Make', 'Top 6 · annual count'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='mf-trend', config={'displayModeBar': False}),
                ], flex=2),
                _panel([
                    _ph('Avg Electric Range by Make', 'Miles · BEVs only'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='mf-range', config={'displayModeBar': False}),
                ]),
            ),
        ], style={'padding': P})

    if tab == 'models':
        return html.Div([
            _row(
                _panel([
                    _ph('Range Distribution', 'Miles · BEVs with known range'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='md-hist', config={'displayModeBar': False}),
                ], flex=2),
                _panel([
                    _ph('Avg Range by Model Year', 'Fleet mean & median'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='md-range-year', config={'displayModeBar': False}),
                ]),
            ),
            _row(
                _panel([
                    _ph('Top 20 Models by Max Range', 'Rated miles'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='md-top-range', config={'displayModeBar': False}),
                ]),
                _panel([
                    _ph('Volume vs Avg Range', 'Bubble size = registration count'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='md-scatter', config={'displayModeBar': False}),
                ]),
            ),
        ], style={'padding': P})

    if tab == 'geo':
        return html.Div([
            _row(
                _panel([
                    _ph('EV Registrations by County', 'Washington State · bubble proportional to fleet size'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='geo-map', config={'displayModeBar': False}),
                ], flex=2),
                _panel([
                    _ph('Top 15 Counties'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='geo-county', config={'displayModeBar': False}),
                ]),
            ),
            _row(
                _panel([
                    _ph('Top 20 Cities'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='geo-city', config={'displayModeBar': False}),
                ]),
                _panel([
                    _ph('Electric Utility Distribution', 'Grid operator share of EV fleet'),
                    dcc.Graph(id='geo-utility', config={'displayModeBar': False}),
                    html.Div(id='geo-utility-legend'),
                ]),
            ),
        ], style={'padding': P})

    if tab == 'global':
        return html.Div([
            _row(
                _panel([
                    _ph('Global EV Sales by Region  2015 – 2024', 'Million units · IEA Global EV Outlook'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='gl-sales', config={'displayModeBar': False}),
                ], flex=2),
                _panel([
                    _ph('Battery Pack Cost Trend', '$/kWh · BloombergNEF'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='gl-battery', config={'displayModeBar': False}),
                ]),
            ),
            _row(
                _panel([
                    _ph('Top Countries by Total Sales', 'Millions of units · selected period'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='gl-countries', config={'displayModeBar': False}),
                ]),
                _panel([
                    _ph('WA State Share of US EV Market', '% of annual US EV registrations'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='gl-wa-vs-global', config={'displayModeBar': False}),
                ]),
            ),
        ], style={'padding': P})


@app.callback(
    Output('kpi-total',  'children'), Output('kpi-total-d', 'children'),
    Output('kpi-bev',    'children'), Output('kpi-bev-d',   'children'),
    Output('kpi-phev',   'children'), Output('kpi-phev-d',  'children'),
    Output('kpi-top',    'children'), Output('kpi-top-d',   'children'),
    Input('yr-slider', 'value'), Input('type-filter', 'value'), Input('make-filter', 'value'),
)
def cb_kpis(yr_range, ev_type, make):
    from dash import html as _html
    d      = _filter(yr_range, ev_type, make)
    yr0, yr1 = yr_range
    total  = len(d)
    bev    = (d['Type'] == 'BEV').sum()
    phev   = (d['Type'] == 'PHEV').sum()
    d_prev = _filter([yr0, max(yr0, yr1 - 1)], ev_type, make)
    t_prev = len(d_prev) if yr1 > yr0 else total
    delta  = (total - t_prev) / t_prev * 100 if t_prev else 0
    top_make  = d['Make'].value_counts().index[0]  if total else 'N/A'
    top_share = d['Make'].value_counts().iloc[0] / total * 100 if total else 0
    sign  = lambda v: ('↑ ' if v >= 0 else '↓ ') + f'{abs(v):.1f}%'
    col   = lambda v: {'color': GREEN if v >= 0 else RED, 'fontSize': '12px'}
    return (
        f'{total:,}',
        _html.Span(sign(delta) + f'  vs {yr0}–{max(yr0, yr1-1)}', style=col(delta)),
        f'{bev:,}',
        _html.Span(f'{bev/total*100:.1f}% of fleet' if total else '—',
                  style={'color': MUTED, 'fontSize': '12px'}),
        f'{phev:,}',
        _html.Span(f'{phev/total*100:.1f}% of fleet' if total else '—',
                  style={'color': MUTED, 'fontSize': '12px'}),
        top_make,
        _html.Span(f'{top_share:.1f}% share', style={'color': MUTED, 'fontSize': '12px'}),
    )


@app.callback(
    Output('ov-year-bar',   'figure'),
    Output('ov-type-pie',   'figure'),
    Output('ov-type-legend','children'),
    Output('ov-make-bar',   'figure'),
    Output('ov-model-bar',  'figure'),
    Input('yr-slider', 'value'), Input('type-filter', 'value'), Input('make-filter', 'value'),
)
def cb_overview(yr_range, ev_type, make):
    d = _filter(yr_range, ev_type, make)
    yr_type = d.groupby(['Year', 'Type']).size().reset_index(name='Count')

    fig1 = go.Figure()
    for t, color in [('BEV', BLUE), ('PHEV', ORANGE)]:
        sub = yr_type[yr_type.Type == t]
        fig1.add_trace(go.Bar(
            x=sub.Year, y=sub.Count, name=t, marker=dict(color=color),
            hovertemplate='<b>%{x}  %{fullData.name}</b>: %{y:,}<extra></extra>',
        ))
    fig1.update_layout(**_chart(height=300), barmode='stack')
    fig1.update_layout(yaxis_title='Registrations', bargap=0.32, margin=dict(l=8,r=8,t=8,b=40))

    tc    = d['Type'].value_counts()
    total = len(d)
    fig2  = go.Figure(go.Pie(
        labels=tc.index, values=tc.values, hole=0.68,
        marker=dict(colors=[BLUE, ORANGE][:len(tc)], line=dict(color=PANEL, width=4)),
        textinfo='none',
        hovertemplate='<b>%{label}</b>: %{value:,}  (%{percent})<extra></extra>',
    ))
    fig2.update_layout(**_chart(height=220), showlegend=False)
    fig2.update_layout(
        margin=dict(l=20, r=20, t=20, b=4),
        annotations=[dict(
            text=f'<b>{total:,}</b><br><span style="font-size:11px">vehicles</span>',
            x=0.5, y=0.5, xref='paper', yref='paper',
            font=dict(size=18, color=TEXT, family='Inter'), showarrow=False,
            align='center',
        )],
    )
    legend_2 = _legend_row([
        (BLUE,   'Battery Electric (BEV)',
         f'{tc.get("BEV",0):,}  ·  {tc.get("BEV",0)/total*100:.1f}%' if total else '—'),
        (ORANGE, 'Plug-in Hybrid (PHEV)',
         f'{tc.get("PHEV",0):,}  ·  {tc.get("PHEV",0)/total*100:.1f}%' if total else '—'),
    ])

    mc = d['Make'].value_counts().head(15).reset_index()
    mc.columns = ['Make', 'Count']
    mc = mc.sort_values('Count')
    fig3 = go.Figure(_bar_h(mc.Count, mc.Make, BLUE, '<b>%{y}</b>: %{x:,}<extra></extra>'))
    fig3.update_layout(**_chart(height=300), showlegend=False)
    fig3.update_layout(margin=dict(l=110, r=12, t=8, b=36))

    model_ct = d['Model'].value_counts().head(15).reset_index()
    model_ct.columns = ['Model', 'Count']
    model_ct = model_ct.sort_values('Count')
    fig4 = go.Figure(_bar_h(model_ct.Count, model_ct.Model, GREEN, '<b>%{y}</b>: %{x:,}<extra></extra>'))
    fig4.update_layout(**_chart(height=300), showlegend=False)
    fig4.update_layout(margin=dict(l=128, r=12, t=8, b=36))

    return fig1, fig2, legend_2, fig3, fig4


@app.callback(
    Output('mf-pie',        'figure'),
    Output('mf-pie-legend', 'children'),
    Output('mf-type-bar',   'figure'),
    Output('mf-trend',      'figure'),
    Output('mf-range',      'figure'),
    Input('yr-slider', 'value'), Input('type-filter', 'value'), Input('make-filter', 'value'),
)
def cb_manufacturers(yr_range, ev_type, make):
    d  = _filter(yr_range, ev_type, make)
    mc = d['Make'].value_counts()
    total = len(d)

    top10  = mc.head(10)
    other  = mc.iloc[10:].sum()
    labels = list(top10.index) + (['Others'] if other > 0 else [])
    values = list(top10.values) + ([other]   if other > 0 else [])

    fig1 = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.60,
        marker=dict(colors=PALETTE[:len(labels)], line=dict(color=PANEL, width=3)),
        textinfo='none',
        hovertemplate='<b>%{label}</b>: %{value:,}  (%{percent})<extra></extra>',
    ))
    fig1.update_layout(**_chart(height=240), showlegend=False)
    fig1.update_layout(margin=dict(l=20, r=20, t=20, b=4))

    legend_1 = _legend_row([
        (PALETTE[i], lbl, f'{v:,}  ·  {v/total*100:.1f}%' if total else '—')
        for i, (lbl, v) in enumerate(zip(labels, values))
    ])

    top12 = mc.head(12).index.tolist()
    sub   = d[d['Make'].isin(top12)]
    mt    = sub.groupby(['Make', 'Type']).size().reset_index(name='Count')
    order = top12[::-1]
    fig2  = go.Figure()
    for t, color in [('BEV', BLUE), ('PHEV', ORANGE)]:
        sub_t = mt[mt.Type == t]
        fig2.add_trace(go.Bar(
            name=t, orientation='h', y=order,
            x=[sub_t[sub_t.Make == m]['Count'].sum() for m in order],
            marker=dict(color=color),
            hovertemplate=f'{t}  <b>%{{y}}</b>: %{{x:,}}<extra></extra>',
        ))
    fig2.update_layout(**_chart(height=340), barmode='stack')
    fig2.update_layout(margin=dict(l=108, r=12, t=28, b=36))

    top6  = mc.head(6).index.tolist()
    trend = d[d['Make'].isin(top6)].groupby(['Year', 'Make']).size().reset_index(name='Count')
    fig3  = go.Figure()
    for i, mk in enumerate(top6):
        s = trend[trend.Make == mk]
        fig3.add_trace(go.Scatter(
            x=s.Year, y=s.Count, name=mk, mode='lines+markers',
            line=dict(color=PALETTE[i], width=2.5),
            marker=dict(size=7, color=PANEL, line=dict(color=PALETTE[i], width=2.5)),
            hovertemplate=f'<b>{mk}</b>  %{{x}}: %{{y:,}}<extra></extra>',
        ))
    fig3.update_layout(**_chart(height=340))
    fig3.update_layout(yaxis_title='Registrations', hovermode='x unified')

    bev_d = d[(d['Type'] == 'BEV') & (d['Range'] > 0)]
    rng   = bev_d.groupby('Make')['Range'].mean().sort_values(ascending=False).head(15)
    rng   = rng.sort_values()
    fig4  = go.Figure(_bar_h(rng.values, rng.index, TEAL, '<b>%{y}</b>: %{x:.0f} mi<extra></extra>'))
    fig4.update_layout(**_chart(height=340), showlegend=False)
    fig4.update_layout(xaxis_title='Avg Range (miles)', margin=dict(l=118, r=12, t=8, b=36))

    return fig1, legend_1, fig2, fig3, fig4


@app.callback(
    Output('md-hist',       'figure'),
    Output('md-range-year', 'figure'),
    Output('md-top-range',  'figure'),
    Output('md-scatter',    'figure'),
    Input('yr-slider', 'value'), Input('type-filter', 'value'), Input('make-filter', 'value'),
)
def cb_models(yr_range, ev_type, make):
    d   = _filter(yr_range, ev_type, make)
    bev = d[(d['Type'] == 'BEV') & (d['Range'] > 0)]
    med = bev['Range'].median() if len(bev) else 0

    fig1 = go.Figure(go.Histogram(
        x=bev['Range'], nbinsx=40,
        marker=dict(color=BLUE, opacity=0.65, line=dict(color=PANEL, width=0.8)),
        hovertemplate='%{x} mi: %{y:,} vehicles<extra></extra>',
    ))
    fig1.update_layout(**_chart(height=300), showlegend=False)
    fig1.update_layout(xaxis_title='Electric Range (miles)', yaxis_title='Vehicles')
    if med:
        fig1.add_vline(x=med, line=dict(color=ORANGE, dash='dash', width=1.5),
                       annotation_text=f'Median  {med:.0f} mi',
                       annotation_font=dict(color=ORANGE, size=12),
                       annotation_position='top right')

    ry  = bev.groupby('Year')['Range'].agg(['mean', 'median']).reset_index()
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=ry.Year, y=ry['mean'], name='Mean',
        mode='lines+markers', line=dict(color=BLUE, width=2.5),
        marker=dict(size=7, color=PANEL, line=dict(color=BLUE, width=2.5)),
        hovertemplate='Mean  %{x}: %{y:.0f} mi<extra></extra>',
    ))
    fig2.add_trace(go.Scatter(
        x=ry.Year, y=ry['median'], name='Median',
        mode='lines+markers', line=dict(color=ORANGE, width=2.5, dash='dot'),
        marker=dict(size=7, color=PANEL, line=dict(color=ORANGE, width=2.5)),
        hovertemplate='Median  %{x}: %{y:.0f} mi<extra></extra>',
    ))
    fig2.update_layout(**_chart(height=300))
    fig2.update_layout(yaxis_title='Range (miles)', hovermode='x unified')

    top_r = (bev.groupby('Model')['Range'].max()
             .sort_values(ascending=False).head(20).reset_index().sort_values('Range'))
    fig3 = go.Figure(go.Bar(
        x=top_r.Range, y=top_r.Model, orientation='h',
        marker=dict(color=PALETTE[:len(top_r)], opacity=0.82,
                    line=dict(color='rgba(0,0,0,0)', width=0)),
        hovertemplate='<b>%{y}</b>: %{x:.0f} mi<extra></extra>',
    ))
    fig3.update_layout(**_chart(height=300), showlegend=False)
    fig3.update_layout(xaxis_title='Max Rated Range (miles)', margin=dict(l=140, r=12, t=8, b=36))

    sd = (bev.groupby('Model')
          .agg(Count=('Range', 'count'), Avg_Range=('Range', 'mean'))
          .reset_index())
    sd = sd[sd.Count >= 50].nlargest(30, 'Count')
    fig4 = go.Figure(go.Scatter(
        x=sd.Avg_Range, y=sd.Count, mode='markers+text',
        text=sd.Model, textfont=dict(size=9, color=MUTED),
        textposition='top center',
        marker=dict(
            size=np.sqrt(sd.Count / sd.Count.max() * 1800) + 8,
            color=sd.Avg_Range,
            colorscale=[[0, _rgba(BLUE, 0.35)], [0.5, BLUE], [1, GREEN]],
            showscale=True,
            colorbar=dict(
                title=dict(text='Range mi', font=dict(color=MUTED, size=11)),
                tickfont=dict(color=MUTED, size=11),
                bgcolor='rgba(0,0,0,0)', thickness=10, len=0.6,
                outlinecolor='rgba(0,0,0,0)',
            ),
            opacity=0.85, line=dict(color=PANEL, width=1.5),
        ),
        hovertemplate='<b>%{text}</b><br>Avg: %{x:.0f} mi  ·  %{y:,} vehicles<extra></extra>',
    ))
    fig4.update_layout(**_chart(height=300), showlegend=False)
    fig4.update_layout(xaxis_title='Avg Range (miles)', yaxis_title='Registrations')

    return fig1, fig2, fig3, fig4


@app.callback(
    Output('geo-map',           'figure'),
    Output('geo-county',        'figure'),
    Output('geo-city',          'figure'),
    Output('geo-utility',       'figure'),
    Output('geo-utility-legend','children'),
    Input('yr-slider', 'value'), Input('type-filter', 'value'), Input('make-filter', 'value'),
)
def cb_geography(yr_range, ev_type, make):
    d = _filter(yr_range, ev_type, make)

    county_ct = d['County'].value_counts().reset_index()
    county_ct.columns = ['County', 'Count']
    county_ct['lat'] = county_ct['County'].map(lambda c: WA_COUNTIES.get(c, (None, None))[0])
    county_ct['lon'] = county_ct['County'].map(lambda c: WA_COUNTIES.get(c, (None, None))[1])
    county_ct = county_ct.dropna(subset=['lat', 'lon'])
    max_c = county_ct['Count'].max()

    fig1 = go.Figure(go.Scattergeo(
        lat=county_ct.lat, lon=county_ct.lon,
        text=county_ct.County, customdata=county_ct.Count,
        mode='markers+text', textfont=dict(size=9, color=TEXT),
        textposition='top center',
        marker=dict(
            size=np.sqrt(county_ct.Count / max_c) * 46 + 6,
            color=county_ct.Count,
            colorscale=[[0, _rgba(BLUE, 0.2)], [0.4, BLUE], [1, PURPLE]],
            opacity=0.82, line=dict(color=PANEL, width=1.5),
            showscale=True,
            colorbar=dict(
                title=dict(text='EVs', font=dict(color=MUTED, size=11)),
                tickfont=dict(color=MUTED, size=11),
                bgcolor='rgba(0,0,0,0)', thickness=10, len=0.55,
                outlinecolor='rgba(0,0,0,0)',
            ),
        ),
        hovertemplate='<b>%{text} County</b><br>%{customdata:,} EVs<extra></extra>',
    ))
    fig1.update_layout(**_chart(height=380))
    fig1.update_layout(
        paper_bgcolor=PANEL,
        geo=dict(
            bgcolor=BG, showframe=False,
            showcoastlines=True, coastlinecolor=SEP,
            showland=True, landcolor='#EDE8F8',
            showocean=True, oceancolor=BG2,
            showlakes=True, lakecolor=BG2,
            lonaxis=dict(range=[-125, -116]),
            lataxis=dict(range=[45.5, 49.5]),
            projection_type='mercator',
        ),
        margin=dict(l=0, r=0, t=8, b=0),
    )

    top_c = county_ct.nlargest(15, 'Count').sort_values('Count')
    fig2 = go.Figure(_bar_h(top_c.Count, top_c.County, BLUE, '<b>%{y}</b>: %{x:,}<extra></extra>'))
    fig2.update_layout(**_chart(height=380), showlegend=False)
    fig2.update_layout(margin=dict(l=102, r=12, t=8, b=36))

    city_ct = d['City'].value_counts().head(20).reset_index()
    city_ct.columns = ['City', 'Count']
    city_ct = city_ct.sort_values('Count')
    fig3 = go.Figure(_bar_h(city_ct.Count, city_ct.City, GREEN, '<b>%{y}</b>: %{x:,}<extra></extra>'))
    fig3.update_layout(**_chart(height=340), showlegend=False)
    fig3.update_layout(margin=dict(l=112, r=12, t=8, b=36))

    util = d['Utility'].dropna().str.split('||').str[0].str.strip()
    uc   = util.value_counts()
    top7 = uc.head(7)
    oth  = uc.iloc[7:].sum()
    u_l  = list(top7.index) + (['Others'] if oth > 0 else [])
    u_v  = list(top7.values) + ([oth]     if oth > 0 else [])
    total_u = sum(u_v)

    fig4 = go.Figure(go.Pie(
        labels=u_l, values=u_v, hole=0.60,
        marker=dict(colors=PALETTE[:len(u_l)], line=dict(color=PANEL, width=3)),
        textinfo='none',
        hovertemplate='<b>%{label}</b>: %{value:,}  (%{percent})<extra></extra>',
    ))
    fig4.update_layout(**_chart(height=240), showlegend=False)
    fig4.update_layout(margin=dict(l=20, r=20, t=20, b=4))

    legend_u = _legend_row([
        (PALETTE[i], lbl, f'{v:,}  ·  {v/total_u*100:.1f}%' if total_u else '—')
        for i, (lbl, v) in enumerate(zip(u_l, u_v))
    ])

    return fig1, fig2, fig3, fig4, legend_u


@app.callback(
    Output('gl-sales',        'figure'),
    Output('gl-battery',      'figure'),
    Output('gl-countries',    'figure'),
    Output('gl-wa-vs-global', 'figure'),
    Input('yr-slider', 'value'), Input('type-filter', 'value'), Input('make-filter', 'value'),
)
def cb_global(yr_range, ev_type, make):
    yr0, yr1 = yr_range
    gl = df_global[(df_global.Year >= yr0) & (df_global.Year <= yr1)]

    region_order = ['Asia-Pacific', 'Europe', 'Americas', 'Rest of World']
    reg_colors   = {'Asia-Pacific': BLUE, 'Europe': GREEN, 'Americas': ORANGE, 'Rest of World': PURPLE}
    reg_trend    = gl.groupby(['Year', 'Region'])['Total'].sum().reset_index()
    fig1 = go.Figure()
    for reg in region_order:
        s = reg_trend[reg_trend.Region == reg]
        if s.empty:
            continue
        c = reg_colors.get(reg, MUTED)
        fig1.add_trace(go.Scatter(
            x=s.Year, y=s.Total, name=reg, stackgroup='one', mode='lines',
            fill='tonexty', line=dict(color=c, width=1.5),
            hovertemplate=f'<b>{reg}</b>  %{{x}}: %{{y:.2f}}M<extra></extra>',
        ))
    fig1.update_layout(**_chart(height=320))
    fig1.update_layout(yaxis_title='Sales (M units)', hovermode='x unified')

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_battery.Year, y=df_battery.Cost_kWh, mode='lines+markers',
        line=dict(color=PURPLE, width=2.5),
        marker=dict(size=7, color=PANEL, line=dict(color=PURPLE, width=2.5)),
        hovertemplate='%{x}: <b>$%{y}</b>/kWh<extra></extra>',
    ))
    fig2.add_hline(y=100, line=dict(color=GREEN, dash='dash', width=1.5),
                   annotation_text='$100 target',
                   annotation_font=dict(color=GREEN, size=12),
                   annotation_position='bottom right')
    fig2.update_layout(**_chart(height=320), showlegend=False)
    fig2.update_layout(yaxis_title='Battery Cost ($/kWh)')

    ctry = gl.groupby('Country')['Total'].sum().sort_values(ascending=False).head(10).reset_index()
    ctry = ctry.sort_values('Total')
    fig3 = go.Figure(go.Bar(
        x=ctry.Total, y=ctry.Country, orientation='h',
        marker=dict(color=PALETTE[:len(ctry)], opacity=0.82,
                    line=dict(color='rgba(0,0,0,0)', width=0)),
        hovertemplate='<b>%{y}</b>: %{x:.2f}M<extra></extra>',
    ))
    fig3.update_layout(**_chart(height=320), showlegend=False)
    fig3.update_layout(xaxis_title='Total Sales (M units)', margin=dict(l=118, r=12, t=8, b=36))

    d_wa   = _filter(yr_range, ev_type, make)
    wa_yr  = d_wa.groupby('Year').size().reset_index(name='WA_Count')
    us_gl  = gl[gl.Country == 'USA'][['Year', 'Total']].rename(columns={'Total': 'US_Sales_M'})
    merged = wa_yr.merge(us_gl, on='Year', how='inner')
    merged['WA_pct'] = merged.WA_Count / (merged.US_Sales_M * 1e6) * 100
    fig4 = go.Figure(go.Bar(
        x=merged.Year, y=merged.WA_pct,
        marker=dict(color=TEAL, opacity=0.8, line=dict(color='rgba(0,0,0,0)', width=0)),
        hovertemplate='%{x}: WA = <b>%{y:.1f}%</b> of US<extra></extra>',
    ))
    fig4.update_layout(**_chart(height=320), showlegend=False)
    fig4.update_layout(yaxis_title='WA Share of US Market (%)', bargap=0.38)

    return fig1, fig2, fig3, fig4
