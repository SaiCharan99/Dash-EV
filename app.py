"""
EV Energy Sector Dashboard
Real data: Washington State EV Population (data.wa.gov) — 280 k+ registrations
Global context: IEA Global EV Outlook 2015-2024
"""

import os
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

BG     = '#09090b'   # zinc-950
CARD   = '#18181b'   # zinc-900
CARD2  = '#27272a'   # zinc-800
BORDER = '#3f3f46'   # zinc-700
TEXT   = '#fafafa'   # zinc-50
MUTED  = '#a1a1aa'   # zinc-400
FAINT  = '#52525b'   # zinc-600

BLUE   = '#3b82f6'
TEAL   = '#14b8a6'
AMBER  = '#f59e0b'
GREEN  = '#22c55e'
RED    = '#ef4444'
PURPLE = '#a855f7'
ORANGE = '#f97316'
CYAN   = '#06b6d4'
ROSE   = '#f43f5e'
LIME   = '#84cc16'
INDIGO = '#6366f1'

PALETTE = [BLUE, TEAL, AMBER, PURPLE, GREEN, RED, ORANGE, CYAN, ROSE, LIME, INDIGO,
           '#e879f9', '#67e8f9', '#bef264', '#fda4af']


def _rgba(hex_color: str, alpha: float) -> str:
    """Convert #rrggbb + alpha to rgba(r,g,b,a) — Plotly-safe."""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'rgba({r},{g},{b},{alpha})'


def _chart(height=310, legend_h=True):
    leg = dict(
        bgcolor='rgba(0,0,0,0)', font=dict(color=MUTED, size=11),
        orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
    ) if legend_h else dict(bgcolor='rgba(0,0,0,0)', font=dict(color=MUTED, size=11))
    return dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, system-ui, sans-serif', color=TEXT, size=12),
        height=height,
        margin=dict(l=10, r=10, t=30, b=36),
        legend=leg,
        colorway=PALETTE,
        xaxis=dict(
            gridcolor=_rgba(BORDER, 0.6), linecolor=BORDER,
            tickfont=dict(color=MUTED, size=11), zeroline=False, showgrid=True,
        ),
        yaxis=dict(
            gridcolor=_rgba(BORDER, 0.6), linecolor=BORDER,
            tickfont=dict(color=MUTED, size=11), zeroline=False, showgrid=True,
        ),
        hoverlabel=dict(bgcolor=CARD2, bordercolor=BORDER, font=dict(color=TEXT, size=12)),
    )


# ══════════════════════════════════════════════════════════════════════════════
# DATA — WASHINGTON STATE (REAL)
# ══════════════════════════════════════════════════════════════════════════════

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'ev_population.csv')

_raw = pd.read_csv(DATA_PATH, low_memory=False)
_raw.columns = [c.strip() for c in _raw.columns]
_raw = _raw.rename(columns={
    'Electric Vehicle Type': 'EV_Type_Full',
    'Electric Range':        'Range',
    'Model Year':            'Year',
    'Vehicle Location':      'Location',
    'Electric Utility':      'Utility',
    'Postal Code':           'ZIP',
})
_raw['Type']  = _raw['EV_Type_Full'].map({
    'Battery Electric Vehicle (BEV)':           'BEV',
    'Plug-in Hybrid Electric Vehicle (PHEV)':   'PHEV',
}).fillna('Other')
_raw['Make']  = _raw['Make'].str.strip().str.title()
_raw['Model'] = _raw['Model'].str.strip().str.title()

DF        = _raw[_raw['Year'].between(2015, 2025)].copy()
ALL_MAKES = ['All'] + sorted(DF['Make'].dropna().unique().tolist())
YEARS_WA  = sorted(DF['Year'].unique().tolist())

WA_COUNTIES = {
    'Adams': (46.97,-118.56), 'Asotin': (46.34,-117.37), 'Benton': (46.22,-119.39),
    'Chelan': (47.82,-120.62), 'Clallam': (48.10,-123.80), 'Clark': (45.79,-122.49),
    'Columbia': (46.31,-117.95), 'Cowlitz': (46.20,-122.77), 'Douglas': (47.63,-119.81),
    'Ferry': (48.60,-118.55), 'Franklin': (46.55,-119.07), 'Garfield': (46.43,-117.58),
    'Grant': (47.22,-119.45), 'Grays Harbor': (47.14,-123.81), 'Island': (48.23,-122.55),
    'Jefferson': (47.82,-124.10), 'King': (47.49,-121.83), 'Kitsap': (47.61,-122.65),
    'Kittitas': (47.12,-120.73), 'Klickitat': (45.87,-120.75), 'Lewis': (46.57,-122.42),
    'Lincoln': (47.58,-118.40), 'Mason': (47.35,-123.22), 'Okanogan': (48.55,-119.71),
    'Pacific': (46.57,-123.91), 'Pend Oreille': (48.55,-117.43), 'Pierce': (47.11,-122.09),
    'San Juan': (48.54,-122.96), 'Skagit': (48.42,-121.76), 'Skamania': (45.82,-121.93),
    'Snohomish': (48.04,-121.76), 'Spokane': (47.62,-117.43), 'Stevens': (48.35,-117.79),
    'Thurston': (46.97,-122.85), 'Wahkiakum': (46.30,-123.43), 'Walla Walla': (46.27,-118.37),
    'Whatcom': (48.84,-122.11), 'Whitman': (46.90,-117.40), 'Yakima': (46.65,-120.45),
}

# ══════════════════════════════════════════════════════════════════════════════
# DATA — GLOBAL CONTEXT (IEA-calibrated)
# ══════════════════════════════════════════════════════════════════════════════

GLOBAL_YEARS = list(range(2015, 2025))
GLOBAL_REGIONS = {
    'Asia-Pacific': ['China', 'Japan', 'South Korea', 'India'],
    'Europe':       ['Germany', 'Norway', 'UK', 'France', 'Netherlands', 'Sweden', 'Rest of EU'],
    'Americas':     ['USA'],
    'Rest of World':['Rest of World'],
}
GLOBAL_SALES = {
    'China':        [0.33,0.51,0.78,1.26,1.21,1.37,3.30,5.90,8.10,9.80],
    'USA':          [0.11,0.16,0.20,0.36,0.33,0.33,0.65,0.92,1.40,1.60],
    'Germany':      [0.023,0.025,0.055,0.067,0.108,0.395,0.356,0.471,0.524,0.580],
    'Norway':       [0.025,0.029,0.033,0.046,0.056,0.076,0.118,0.138,0.163,0.175],
    'UK':           [0.015,0.025,0.047,0.060,0.075,0.175,0.267,0.267,0.314,0.350],
    'France':       [0.022,0.022,0.036,0.044,0.061,0.186,0.219,0.210,0.245,0.280],
    'Netherlands':  [0.043,0.024,0.011,0.025,0.068,0.098,0.170,0.230,0.250,0.270],
    'South Korea':  [0.011,0.013,0.026,0.031,0.038,0.056,0.103,0.163,0.210,0.250],
    'Japan':        [0.050,0.048,0.054,0.059,0.071,0.098,0.130,0.145,0.170,0.200],
    'India':        [0.002,0.003,0.004,0.006,0.008,0.015,0.040,0.085,0.150,0.210],
    'Rest of EU':   [0.015,0.020,0.030,0.045,0.065,0.180,0.280,0.340,0.380,0.420],
    'Rest of World':[0.008,0.012,0.018,0.025,0.035,0.060,0.110,0.180,0.260,0.340],
}
BATTERY = dict(
    Year          =[2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025],
    Cost_kWh      =[680, 540, 373, 295, 230, 185, 156, 137, 132, 138, 139, 115, 100],
    Energy_Density=[150, 160, 175, 185, 200, 215, 235, 255, 275, 295, 315, 340, 360],
    Avg_Range_km  =[180, 195, 215, 240, 265, 290, 320, 355, 385, 415, 450, 490, 530],
)
df_battery = pd.DataFrame(BATTERY)

def _get_region(c):
    return next((r for r, cs in GLOBAL_REGIONS.items() if c in cs), 'Rest of World')

df_global = pd.DataFrame([
    dict(Year=y, Country=c, Region=_get_region(c), Total=v)
    for c, vs in GLOBAL_SALES.items()
    for y, v in zip(GLOBAL_YEARS, vs)
])

# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════

def _panel(children, flex=1, style=None):
    s = {
        'background': CARD, 'border': f'1px solid {BORDER}', 'borderRadius': '8px',
        'padding': '0', 'flex': str(flex), 'minWidth': '0', 'overflow': 'hidden',
    }
    if style:
        s.update(style)
    return html.Div(children, style=s)


def _panel_header(title, subtitle=''):
    return html.Div([
        html.Div(title, style={
            'fontSize': '13px', 'fontWeight': '600', 'color': TEXT,
            'padding': '14px 16px 0', 'letterSpacing': '-0.1px',
        }),
        html.Div(subtitle, style={
            'fontSize': '11px', 'color': MUTED, 'padding': '2px 16px 8px',
        }) if subtitle else '',
    ])


def _row(*children, gap='12px', mb='12px', wrap=False):
    return html.Div(list(children), style={
        'display': 'flex', 'gap': gap, 'marginBottom': mb,
        'flexWrap': 'wrap' if wrap else 'nowrap',
    })


def _kpi_card(label, value_id, delta_id=None, accent=BLUE):
    return html.Div([
        html.Div(label, style={
            'fontSize': '11px', 'fontWeight': '500', 'color': MUTED,
            'textTransform': 'uppercase', 'letterSpacing': '0.8px', 'marginBottom': '10px',
        }),
        html.Div(id=value_id, style={
            'fontSize': '2rem', 'fontWeight': '700', 'color': TEXT,
            'lineHeight': '1', 'fontVariantNumeric': 'tabular-nums',
        }),
        html.Div(id=delta_id, style={
            'fontSize': '11px', 'fontWeight': '500', 'color': MUTED, 'marginTop': '4px',
        }) if delta_id else '',
        html.Div(style={
            'height': '2px', 'background': accent, 'borderRadius': '1px',
            'marginTop': '12px', 'width': '28px',
        }),
    ], style={
        'background': CARD, 'border': f'1px solid {BORDER}', 'borderRadius': '8px',
        'padding': '16px 18px', 'flex': '1', 'minWidth': '160px',
    })


def _tab_s():
    return {
        'background': CARD, 'border': f'1px solid {BORDER}', 'borderBottom': 'none',
        'borderRadius': '6px 6px 0 0', 'color': MUTED, 'fontSize': '12px',
        'fontWeight': '500', 'padding': '9px 16px', 'marginRight': '3px',
        'fontFamily': 'Inter, system-ui, sans-serif',
    }


def _tab_sel():
    s = _tab_s()
    s.update({'background': CARD2, 'borderColor': BLUE, 'color': TEXT, 'fontWeight': '600'})
    return s


def _tab_body(children):
    return html.Div(children, style={
        'background': BG, 'border': f'1px solid {BORDER}',
        'borderRadius': '0 6px 6px 6px', 'padding': '16px',
    })


# ══════════════════════════════════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════════════════════════════════

app = dash.Dash(__name__, suppress_callback_exceptions=True, title='EV Dashboard')
server = app.server

_yr_marks = {
    y: {'label': str(y), 'style': {'color': MUTED, 'fontSize': '10px'}}
    for y in YEARS_WA if y % 2 == 1
}

app.layout = html.Div([

    # ── Header ────────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Div('EV Market Dashboard', style={
                'fontSize': '15px', 'fontWeight': '700', 'color': TEXT,
                'letterSpacing': '-0.3px',
            }),
            html.Div('Washington State · 280 k+ registrations · IEA global context',
                     style={'fontSize': '11px', 'color': MUTED, 'marginTop': '2px'}),
        ]),
        html.Div('data.wa.gov  |  IEA EV Outlook', style={
            'fontSize': '11px', 'color': FAINT,
        }),
    ], style={
        'background': CARD, 'borderBottom': f'1px solid {BORDER}',
        'padding': '14px 28px', 'display': 'flex', 'alignItems': 'center',
        'justifyContent': 'space-between', 'position': 'sticky', 'top': '0', 'zIndex': '100',
    }),

    # ── KPI Row ───────────────────────────────────────────────────────────────
    html.Div([
        _kpi_card('Total Registered EVs',  'kpi-total', 'kpi-total-d', BLUE),
        _kpi_card('Battery Electric (BEV)','kpi-bev',   'kpi-bev-d',   TEAL),
        _kpi_card('Plug-in Hybrid (PHEV)', 'kpi-phev',  'kpi-phev-d',  AMBER),
        _kpi_card('Market Leader',         'kpi-top',   'kpi-top-d',   PURPLE),
    ], style={'display': 'flex', 'gap': '12px', 'padding': '18px 28px 0', 'flexWrap': 'wrap'}),

    # ── Filter Bar ────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Div('Model Year', style={
                'fontSize': '10px', 'color': MUTED, 'fontWeight': '600',
                'textTransform': 'uppercase', 'letterSpacing': '0.7px', 'marginBottom': '8px',
            }),
            dcc.RangeSlider(
                id='yr-slider', min=2015, max=2025, step=1, value=[2015, 2025],
                marks=_yr_marks, allowCross=False,
                tooltip={'placement': 'bottom', 'always_visible': False},
            ),
        ], style={'flex': '3', 'minWidth': '240px'}),
        html.Div([
            html.Div('EV Type', style={
                'fontSize': '10px', 'color': MUTED, 'fontWeight': '600',
                'textTransform': 'uppercase', 'letterSpacing': '0.7px', 'marginBottom': '7px',
            }),
            dcc.RadioItems(
                id='type-filter', value='All', inline=True,
                options=[{'label': ' All', 'value': 'All'},
                         {'label': ' BEV', 'value': 'BEV'},
                         {'label': ' PHEV', 'value': 'PHEV'}],
                inputStyle={'marginRight': '4px'},
                labelStyle={'marginRight': '14px', 'color': MUTED, 'fontSize': '12px'},
            ),
        ], style={'flex': '1'}),
        html.Div([
            html.Div('Make', style={
                'fontSize': '10px', 'color': MUTED, 'fontWeight': '600',
                'textTransform': 'uppercase', 'letterSpacing': '0.7px', 'marginBottom': '6px',
            }),
            dcc.Dropdown(
                id='make-filter',
                options=[{'label': m, 'value': m} for m in ALL_MAKES],
                value='All', clearable=False,
                style={'background': CARD2, 'border': f'1px solid {BORDER}', 'minWidth': '150px'},
            ),
        ], style={'flex': '1'}),
    ], style={
        'display': 'flex', 'alignItems': 'center', 'gap': '28px',
        'padding': '14px 24px', 'background': CARD, 'border': f'1px solid {BORDER}',
        'borderRadius': '8px', 'margin': '16px 28px 0', 'flexWrap': 'wrap',
    }),

    # ── Tabs ──────────────────────────────────────────────────────────────────
    html.Div([
        dcc.Tabs(id='main-tabs', value='overview', children=[

            dcc.Tab(label='Fleet Overview',  value='overview',
                    style=_tab_s(), selected_style=_tab_sel(),
                    children=_tab_body([
                        _row(
                            _panel([_panel_header('Registrations by Model Year', 'Annual fleet growth · BEV vs PHEV'),
                                    dcc.Graph(id='ov-year-bar', config={'displayModeBar': False})], flex=2),
                            _panel([_panel_header('BEV vs PHEV Split', 'Battery vs Plug-in Hybrid'),
                                    dcc.Graph(id='ov-type-pie', config={'displayModeBar': False})], flex=1),
                        ),
                        _row(
                            _panel([_panel_header('Top 15 Makes', 'By registered vehicle count'),
                                    dcc.Graph(id='ov-make-bar', config={'displayModeBar': False})]),
                            _panel([_panel_header('Top 15 Models', 'Most popular EV models'),
                                    dcc.Graph(id='ov-model-bar', config={'displayModeBar': False})]),
                        ),
                    ])),

            dcc.Tab(label='Manufacturers', value='mfr',
                    style=_tab_s(), selected_style=_tab_sel(),
                    children=_tab_body([
                        _row(
                            _panel([_panel_header('Market Share', '% of total registrations'),
                                    dcc.Graph(id='mf-pie', config={'displayModeBar': False})], flex='1.2'),
                            _panel([_panel_header('BEV vs PHEV by Make', 'Top 12 manufacturers'),
                                    dcc.Graph(id='mf-type-bar', config={'displayModeBar': False})], flex=2),
                        ),
                        _row(
                            _panel([_panel_header('Registration Trend by Make', 'Top 6 · annual count'),
                                    dcc.Graph(id='mf-trend', config={'displayModeBar': False})], flex=2),
                            _panel([_panel_header('Avg Electric Range by Make', 'Miles · BEV registrations only'),
                                    dcc.Graph(id='mf-range', config={'displayModeBar': False})], flex=1),
                        ),
                    ])),

            dcc.Tab(label='Models & Range', value='models',
                    style=_tab_s(), selected_style=_tab_sel(),
                    children=_tab_body([
                        _row(
                            _panel([_panel_header('Range Distribution', 'Miles · BEVs with known range'),
                                    dcc.Graph(id='md-hist', config={'displayModeBar': False})], flex=2),
                            _panel([_panel_header('Avg Range by Model Year', 'Fleet mean & median · BEV'),
                                    dcc.Graph(id='md-range-year', config={'displayModeBar': False})], flex=1),
                        ),
                        _row(
                            _panel([_panel_header('Top 20 Models by Max Range', 'Rated range in miles'),
                                    dcc.Graph(id='md-top-range', config={'displayModeBar': False})]),
                            _panel([_panel_header('Volume vs Avg Range', 'Bubble size = registration count'),
                                    dcc.Graph(id='md-scatter', config={'displayModeBar': False})]),
                        ),
                    ])),

            dcc.Tab(label='Geography', value='geo',
                    style=_tab_s(), selected_style=_tab_sel(),
                    children=_tab_body([
                        _row(
                            _panel([_panel_header('EV Registrations by County', 'Bubble size proportional to count'),
                                    dcc.Graph(id='geo-map', config={'displayModeBar': False})], flex=2),
                            _panel([_panel_header('Top 15 Counties', 'Registered EV count'),
                                    dcc.Graph(id='geo-county', config={'displayModeBar': False})], flex=1),
                        ),
                        _row(
                            _panel([_panel_header('Top 20 Cities'),
                                    dcc.Graph(id='geo-city', config={'displayModeBar': False})]),
                            _panel([_panel_header('Electric Utility Distribution', 'Grid operator share'),
                                    dcc.Graph(id='geo-utility', config={'displayModeBar': False})]),
                        ),
                    ])),

            dcc.Tab(label='Global Context', value='global',
                    style=_tab_s(), selected_style=_tab_sel(),
                    children=_tab_body([
                        _row(
                            _panel([_panel_header('Global EV Sales by Region 2015–2024', 'Million units · IEA'),
                                    dcc.Graph(id='gl-sales', config={'displayModeBar': False})], flex=2),
                            _panel([_panel_header('Battery Pack Cost', '$/kWh · BloombergNEF'),
                                    dcc.Graph(id='gl-battery', config={'displayModeBar': False})], flex=1),
                        ),
                        _row(
                            _panel([_panel_header('Top Countries by Total Sales', 'Millions of units · period total'),
                                    dcc.Graph(id='gl-countries', config={'displayModeBar': False})]),
                            _panel([_panel_header('WA State Share of US EV Market', '% of annual US sales'),
                                    dcc.Graph(id='gl-wa-vs-global', config={'displayModeBar': False})]),
                        ),
                    ])),

        ], colors={'border': BORDER, 'primary': BLUE, 'background': BG}),
    ], style={'margin': '0 28px'}),

    html.Div('EV Market Dashboard  ·  Washington State DOL  ·  IEA Global EV Outlook',
             style={
                 'textAlign': 'center', 'padding': '16px', 'color': FAINT,
                 'fontSize': '11px', 'marginTop': '16px', 'borderTop': f'1px solid {BORDER}',
             }),

], style={'backgroundColor': BG, 'minHeight': '100vh', 'fontFamily': 'Inter, system-ui, sans-serif'})


# ══════════════════════════════════════════════════════════════════════════════
# FILTER HELPER
# ══════════════════════════════════════════════════════════════════════════════

def _filter(yr_range, ev_type, make):
    yr0, yr1 = yr_range
    d = DF[(DF['Year'] >= yr0) & (DF['Year'] <= yr1)]
    if ev_type != 'All':
        d = d[d['Type'] == ev_type]
    if make != 'All':
        d = d[d['Make'] == make]
    return d


# ══════════════════════════════════════════════════════════════════════════════
# KPIs
# ══════════════════════════════════════════════════════════════════════════════

@app.callback(
    Output('kpi-total',   'children'), Output('kpi-total-d',  'children'),
    Output('kpi-bev',     'children'), Output('kpi-bev-d',    'children'),
    Output('kpi-phev',    'children'), Output('kpi-phev-d',   'children'),
    Output('kpi-top',     'children'), Output('kpi-top-d',    'children'),
    Input('yr-slider',   'value'),
    Input('type-filter', 'value'),
    Input('make-filter', 'value'),
)
def cb_kpis(yr_range, ev_type, make):
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

    arrow = lambda v: ('+ ' if v >= 0 else '- ') + f'{abs(v):.1f}%'
    col   = lambda v: {'color': GREEN if v >= 0 else RED}

    return (
        f'{total:,}',
        html.Span(arrow(delta) + f'  vs {yr0}–{max(yr0, yr1-1)}', style=col(delta)),
        f'{bev:,}',
        html.Span(f'{bev/total*100:.1f}% of fleet' if total else '—', style={'color': MUTED}),
        f'{phev:,}',
        html.Span(f'{phev/total*100:.1f}% of fleet' if total else '—', style={'color': MUTED}),
        top_make,
        html.Span(f'{top_share:.1f}% share', style={'color': MUTED}),
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — FLEET OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

@app.callback(
    Output('ov-year-bar',  'figure'),
    Output('ov-type-pie',  'figure'),
    Output('ov-make-bar',  'figure'),
    Output('ov-model-bar', 'figure'),
    Input('yr-slider',   'value'),
    Input('type-filter', 'value'),
    Input('make-filter', 'value'),
)
def cb_overview(yr_range, ev_type, make):
    d = _filter(yr_range, ev_type, make)

    # Registrations by year
    yr_type = d.groupby(['Year', 'Type']).size().reset_index(name='Count')
    fig1 = go.Figure()
    for t, color in [('BEV', BLUE), ('PHEV', AMBER)]:
        sub = yr_type[yr_type.Type == t]
        fig1.add_trace(go.Bar(
            x=sub.Year, y=sub.Count, name=t,
            marker=dict(color=color),
            hovertemplate='<b>%{x}  %{fullData.name}</b>: %{y:,}<extra></extra>',
        ))
    fig1.update_layout(**_chart(height=290), barmode='stack')
    fig1.update_layout(yaxis_title='Registrations', bargap=0.3)

    # BEV vs PHEV donut
    tc = d['Type'].value_counts()
    fig2 = go.Figure(go.Pie(
        labels=tc.index, values=tc.values, hole=0.58,
        marker=dict(colors=[BLUE, AMBER], line=dict(color=BG, width=2)),
        textinfo='label+percent', textfont=dict(size=11, color=TEXT),
        hovertemplate='<b>%{label}</b>: %{value:,}  (%{percent})<extra></extra>',
    ))
    fig2.update_layout(**_chart(height=290), showlegend=False)
    fig2.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        annotations=[dict(
            text=f'{len(d):,}', x=0.5, y=0.5,
            font=dict(size=14, color=TEXT, family='Inter'), showarrow=False,
        )],
    )

    # Top 15 makes
    mc = d['Make'].value_counts().head(15).reset_index()
    mc.columns = ['Make', 'Count']
    mc = mc.sort_values('Count')
    fig3 = go.Figure(go.Bar(
        x=mc.Count, y=mc.Make, orientation='h',
        marker=dict(color=BLUE, opacity=0.85),
        hovertemplate='<b>%{y}</b>: %{x:,}<extra></extra>',
    ))
    fig3.update_layout(**_chart(height=290), showlegend=False)
    fig3.update_layout(margin=dict(l=110, r=10, t=20, b=30))

    # Top 15 models — two-tone: top 3 highlighted
    model_ct = d['Model'].value_counts().head(15).reset_index()
    model_ct.columns = ['Model', 'Count']
    model_ct = model_ct.sort_values('Count')
    colors_m = [TEAL if i >= 12 else _rgba(TEAL, 0.4) for i in range(len(model_ct))]
    fig4 = go.Figure(go.Bar(
        x=model_ct.Count, y=model_ct.Model, orientation='h',
        marker=dict(color=colors_m),
        hovertemplate='<b>%{y}</b>: %{x:,}<extra></extra>',
    ))
    fig4.update_layout(**_chart(height=290), showlegend=False)
    fig4.update_layout(margin=dict(l=130, r=10, t=20, b=30))

    return fig1, fig2, fig3, fig4


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MANUFACTURERS
# ══════════════════════════════════════════════════════════════════════════════

@app.callback(
    Output('mf-pie',      'figure'),
    Output('mf-type-bar', 'figure'),
    Output('mf-trend',    'figure'),
    Output('mf-range',    'figure'),
    Input('yr-slider',   'value'),
    Input('type-filter', 'value'),
    Input('make-filter', 'value'),
)
def cb_manufacturers(yr_range, ev_type, make):
    d = _filter(yr_range, ev_type, make)
    mc = d['Make'].value_counts()

    # Market share donut
    top10  = mc.head(10)
    other  = mc.iloc[10:].sum()
    labels = list(top10.index) + (['Others'] if other > 0 else [])
    values = list(top10.values) + ([other]   if other > 0 else [])
    fig1 = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.52,
        marker=dict(colors=PALETTE[:len(labels)], line=dict(color=BG, width=2)),
        textinfo='label+percent', textfont=dict(size=10, color=TEXT),
        insidetextorientation='radial',
        hovertemplate='<b>%{label}</b>: %{value:,}  (%{percent})<extra></extra>',
    ))
    fig1.update_layout(**_chart(height=320), showlegend=False)
    fig1.update_layout(margin=dict(l=10, r=10, t=20, b=10))

    # BEV vs PHEV by make
    top12 = mc.head(12).index.tolist()
    sub   = d[d['Make'].isin(top12)]
    mt    = sub.groupby(['Make', 'Type']).size().reset_index(name='Count')
    order = top12[::-1]
    fig2  = go.Figure()
    for t, color in [('BEV', BLUE), ('PHEV', AMBER)]:
        sub_t = mt[mt.Type == t]
        fig2.add_trace(go.Bar(
            name=t, orientation='h',
            y=order,
            x=[sub_t[sub_t.Make == m]['Count'].sum() for m in order],
            marker=dict(color=color),
            hovertemplate=f'{t}  <b>%{{y}}</b>: %{{x:,}}<extra></extra>',
        ))
    fig2.update_layout(**_chart(height=320), barmode='stack')
    fig2.update_layout(margin=dict(l=110, r=10, t=28, b=30))

    # Registration trend — top 6
    top6  = mc.head(6).index.tolist()
    trend = d[d['Make'].isin(top6)].groupby(['Year', 'Make']).size().reset_index(name='Count')
    fig3  = go.Figure()
    for i, mk in enumerate(top6):
        s = trend[trend.Make == mk]
        fig3.add_trace(go.Scatter(
            x=s.Year, y=s.Count, name=mk, mode='lines+markers',
            line=dict(color=PALETTE[i], width=2),
            marker=dict(size=5),
            hovertemplate=f'<b>{mk}</b>  %{{x}}: %{{y:,}}<extra></extra>',
        ))
    fig3.update_layout(**_chart(height=320))
    fig3.update_layout(yaxis_title='Registrations', hovermode='x unified')

    # Avg range by make (BEV only)
    bev_d = d[(d['Type'] == 'BEV') & (d['Range'] > 0)]
    rng   = bev_d.groupby('Make')['Range'].mean().sort_values(ascending=False).head(15)
    rng   = rng.sort_values()
    bar_colors = [TEAL if v >= rng.median() else _rgba(TEAL, 0.4) for v in rng.values]
    fig4 = go.Figure(go.Bar(
        x=rng.values, y=rng.index, orientation='h',
        marker=dict(color=bar_colors),
        hovertemplate='<b>%{y}</b>: %{x:.0f} mi<extra></extra>',
    ))
    fig4.update_layout(**_chart(height=320), showlegend=False)
    fig4.update_layout(xaxis_title='Avg Range (miles)', margin=dict(l=120, r=10, t=20, b=30))

    return fig1, fig2, fig3, fig4


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — MODELS & RANGE
# ══════════════════════════════════════════════════════════════════════════════

@app.callback(
    Output('md-hist',       'figure'),
    Output('md-range-year', 'figure'),
    Output('md-top-range',  'figure'),
    Output('md-scatter',    'figure'),
    Input('yr-slider',   'value'),
    Input('type-filter', 'value'),
    Input('make-filter', 'value'),
)
def cb_models(yr_range, ev_type, make):
    d   = _filter(yr_range, ev_type, make)
    bev = d[(d['Type'] == 'BEV') & (d['Range'] > 0)]

    # Range histogram
    med = bev['Range'].median() if len(bev) else 0
    fig1 = go.Figure(go.Histogram(
        x=bev['Range'], nbinsx=40,
        marker=dict(color=BLUE, opacity=0.75, line=dict(color=BG, width=0.5)),
        hovertemplate='%{x} mi: %{y:,} vehicles<extra></extra>',
    ))
    fig1.update_layout(**_chart(height=290), showlegend=False)
    fig1.update_layout(xaxis_title='Electric Range (miles)', yaxis_title='Vehicles')
    if med:
        fig1.add_vline(
            x=med, line=dict(color=AMBER, dash='dash', width=1.5),
            annotation_text=f'Median  {med:.0f} mi',
            annotation_font=dict(color=AMBER, size=11),
            annotation_position='top right',
        )

    # Avg range by year
    ry  = bev.groupby('Year')['Range'].agg(['mean', 'median']).reset_index()
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=ry.Year, y=ry['mean'], name='Mean',
        mode='lines+markers', line=dict(color=BLUE, width=2.5),
        marker=dict(size=6),
        hovertemplate='Mean  %{x}: %{y:.0f} mi<extra></extra>',
    ))
    fig2.add_trace(go.Scatter(
        x=ry.Year, y=ry['median'], name='Median',
        mode='lines+markers', line=dict(color=AMBER, width=2, dash='dot'),
        marker=dict(size=6),
        hovertemplate='Median  %{x}: %{y:.0f} mi<extra></extra>',
    ))
    fig2.update_layout(**_chart(height=290))
    fig2.update_layout(yaxis_title='Range (miles)', hovermode='x unified')

    # Top 20 models by max range
    top_r = (bev.groupby('Model')['Range'].max()
             .sort_values(ascending=False).head(20).reset_index()
             .sort_values('Range'))
    fig3 = go.Figure(go.Bar(
        x=top_r.Range, y=top_r.Model, orientation='h',
        marker=dict(color=PALETTE[:len(top_r)], opacity=0.85),
        hovertemplate='<b>%{y}</b>: %{x:.0f} mi<extra></extra>',
    ))
    fig3.update_layout(**_chart(height=290), showlegend=False)
    fig3.update_layout(xaxis_title='Max Rated Range (miles)', margin=dict(l=140, r=10, t=20, b=30))

    # Scatter: count vs avg range
    sd = (bev.groupby('Model')
          .agg(Count=('Range', 'count'), Avg_Range=('Range', 'mean'))
          .reset_index())
    sd = sd[sd.Count >= 50].nlargest(30, 'Count')
    fig4 = go.Figure(go.Scatter(
        x=sd.Avg_Range, y=sd.Count,
        mode='markers+text',
        text=sd.Model,
        textfont=dict(size=9, color=MUTED),
        textposition='top center',
        marker=dict(
            size=np.sqrt(sd.Count / sd.Count.max() * 2000) + 7,
            color=sd.Avg_Range,
            colorscale=[[0, _rgba(BLUE, 0.5)], [0.5, BLUE], [1.0, TEAL]],
            showscale=True,
            colorbar=dict(
                title=dict(text='Range', font=dict(color=MUTED, size=10)),
                tickfont=dict(color=MUTED, size=10),
                bgcolor='rgba(0,0,0,0)', thickness=8, len=0.6,
            ),
            opacity=0.8, line=dict(color=BG, width=1),
        ),
        hovertemplate='<b>%{text}</b><br>Avg: %{x:.0f} mi  |  Count: %{y:,}<extra></extra>',
    ))
    fig4.update_layout(**_chart(height=290), showlegend=False)
    fig4.update_layout(xaxis_title='Avg Range (miles)', yaxis_title='Registrations')

    return fig1, fig2, fig3, fig4


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — GEOGRAPHY
# ══════════════════════════════════════════════════════════════════════════════

@app.callback(
    Output('geo-map',     'figure'),
    Output('geo-county',  'figure'),
    Output('geo-city',    'figure'),
    Output('geo-utility', 'figure'),
    Input('yr-slider',   'value'),
    Input('type-filter', 'value'),
    Input('make-filter', 'value'),
)
def cb_geography(yr_range, ev_type, make):
    d = _filter(yr_range, ev_type, make)

    # County bubble map
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
            size=np.sqrt(county_ct.Count / max_c) * 42 + 5,
            color=county_ct.Count,
            colorscale=[[0, _rgba(BLUE, 0.3)], [0.5, BLUE], [1.0, TEAL]],
            opacity=0.8, line=dict(color=BG, width=0.5),
            showscale=True,
            colorbar=dict(
                title=dict(text='EVs', font=dict(color=MUTED, size=10)),
                tickfont=dict(color=MUTED, size=10),
                bgcolor='rgba(0,0,0,0)', thickness=8, len=0.6,
            ),
        ),
        hovertemplate='<b>%{text} County</b><br>EVs: %{customdata:,}<extra></extra>',
    ))
    fig1.update_layout(**_chart(height=360))
    fig1.update_layout(
        geo=dict(
            bgcolor='rgba(0,0,0,0)', showframe=False, showcoastlines=True,
            coastlinecolor=BORDER, showland=True, landcolor=CARD2,
            showocean=True, oceancolor=BG, showlakes=True, lakecolor=BG,
            lonaxis=dict(range=[-125, -116]), lataxis=dict(range=[45.5, 49.5]),
            projection_type='mercator',
        ),
        margin=dict(l=0, r=0, t=10, b=0),
    )

    # Top 15 counties
    top_c = county_ct.nlargest(15, 'Count').sort_values('Count')
    fig2 = go.Figure(go.Bar(
        x=top_c.Count, y=top_c.County, orientation='h',
        marker=dict(color=PALETTE[:len(top_c)], opacity=0.85),
        hovertemplate='<b>%{y}</b>: %{x:,}<extra></extra>',
    ))
    fig2.update_layout(**_chart(height=360), showlegend=False)
    fig2.update_layout(margin=dict(l=100, r=10, t=20, b=30))

    # Top 20 cities
    city_ct = d['City'].value_counts().head(20).reset_index()
    city_ct.columns = ['City', 'Count']
    city_ct = city_ct.sort_values('Count')
    bar_c = [TEAL if i >= 17 else _rgba(TEAL, 0.4) for i in range(len(city_ct))]
    fig3 = go.Figure(go.Bar(
        x=city_ct.Count, y=city_ct.City, orientation='h',
        marker=dict(color=bar_c),
        hovertemplate='<b>%{y}</b>: %{x:,}<extra></extra>',
    ))
    fig3.update_layout(**_chart(height=360), showlegend=False)
    fig3.update_layout(margin=dict(l=110, r=10, t=20, b=30))

    # Electric utility donut
    util = d['Utility'].dropna().str.split('||').str[0].str.strip()
    uc   = util.value_counts()
    top8 = uc.head(8)
    oth  = uc.iloc[8:].sum()
    u_l  = list(top8.index) + (['Others'] if oth > 0 else [])
    u_v  = list(top8.values) + ([oth]      if oth > 0 else [])
    fig4 = go.Figure(go.Pie(
        labels=u_l, values=u_v, hole=0.45,
        marker=dict(colors=PALETTE[:len(u_l)], line=dict(color=BG, width=2)),
        textinfo='label+percent', textfont=dict(size=9, color=TEXT),
        hovertemplate='<b>%{label}</b>: %{value:,}  (%{percent})<extra></extra>',
    ))
    fig4.update_layout(**_chart(height=360), showlegend=False)
    fig4.update_layout(margin=dict(l=10, r=10, t=20, b=10))

    return fig1, fig2, fig3, fig4


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — GLOBAL CONTEXT
# ══════════════════════════════════════════════════════════════════════════════

@app.callback(
    Output('gl-sales',        'figure'),
    Output('gl-battery',      'figure'),
    Output('gl-countries',    'figure'),
    Output('gl-wa-vs-global', 'figure'),
    Input('yr-slider',   'value'),
    Input('type-filter', 'value'),
    Input('make-filter', 'value'),
)
def cb_global(yr_range, ev_type, make):
    yr0, yr1 = yr_range
    gl  = df_global[(df_global.Year >= yr0) & (df_global.Year <= yr1)]
    bat = df_battery

    # Global sales stacked area
    reg_trend   = gl.groupby(['Year', 'Region'])['Total'].sum().reset_index()
    region_order = ['Asia-Pacific', 'Europe', 'Americas', 'Rest of World']
    reg_colors   = {'Asia-Pacific': BLUE, 'Europe': TEAL, 'Americas': AMBER, 'Rest of World': PURPLE}
    fig1 = go.Figure()
    for reg in region_order:
        s = reg_trend[reg_trend.Region == reg]
        if s.empty:
            continue
        fig1.add_trace(go.Scatter(
            x=s.Year, y=s.Total, name=reg, stackgroup='one', mode='lines',
            fill='tonexty', line=dict(color=reg_colors.get(reg, MUTED), width=1.5),
            hovertemplate=f'<b>{reg}</b>  %{{x}}: %{{y:.2f}}M<extra></extra>',
        ))
    fig1.update_layout(**_chart(height=310))
    fig1.update_layout(yaxis_title='Sales (M units)', hovermode='x unified')

    # Battery cost
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=bat.Year, y=bat.Cost_kWh, mode='lines+markers',
        line=dict(color=PURPLE, width=2.5), marker=dict(size=6, color=PURPLE),
        hovertemplate='%{x}: <b>$%{y}</b>/kWh<extra></extra>',
    ))
    fig2.add_hline(
        y=100, line=dict(color=GREEN, dash='dash', width=1.5),
        annotation_text='$100 target',
        annotation_font=dict(color=GREEN, size=11),
        annotation_position='bottom right',
    )
    fig2.update_layout(**_chart(height=310), showlegend=False)
    fig2.update_layout(yaxis_title='Battery Cost ($/kWh)')

    # Top countries bar
    ctry = gl.groupby('Country')['Total'].sum().sort_values(ascending=False).head(10).reset_index()
    ctry = ctry.sort_values('Total')
    fig3 = go.Figure(go.Bar(
        x=ctry.Total, y=ctry.Country, orientation='h',
        marker=dict(color=PALETTE[:len(ctry)], opacity=0.85),
        hovertemplate='<b>%{y}</b>: %{x:.2f}M<extra></extra>',
    ))
    fig3.update_layout(**_chart(height=310), showlegend=False)
    fig3.update_layout(xaxis_title='Total Sales (M units)', margin=dict(l=120, r=10, t=20, b=30))

    # WA share of US market
    d_wa   = _filter(yr_range, ev_type, make)
    wa_yr  = d_wa.groupby('Year').size().reset_index(name='WA_Count')
    us_gl  = gl[gl.Country == 'USA'][['Year', 'Total']].rename(columns={'Total': 'US_Sales_M'})
    merged = wa_yr.merge(us_gl, on='Year', how='inner')
    merged['WA_pct'] = merged.WA_Count / (merged.US_Sales_M * 1e6) * 100

    fig4 = go.Figure(go.Bar(
        x=merged.Year, y=merged.WA_pct,
        marker=dict(color=BLUE, opacity=0.85),
        hovertemplate='%{x}: WA = <b>%{y:.1f}%</b> of US sales<extra></extra>',
    ))
    fig4.update_layout(**_chart(height=310), showlegend=False)
    fig4.update_layout(yaxis_title='WA Share of US EV Market (%)', bargap=0.35)

    return fig1, fig2, fig3, fig4


# ══════════════════════════════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    app.run(debug=True, port=8050)
