import os
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np

BG       = '#F5F5F7'
PANEL    = '#FFFFFF'
BG2      = '#F2F2F7'

TEXT      = '#1C1C1E'
SECONDARY = '#48484A'
MUTED     = '#6C6C70'
SUBTLE    = '#8E8E93'

SEP      = '#E5E5EA'

BLUE   = '#007AFF'
GREEN  = '#34C759'
ORANGE = '#FF9500'
RED    = '#FF3B30'
PURPLE = '#AF52DE'
TEAL   = '#32ADE6'

NAV_BG   = '#1C1C1E'
NAV_TEXT = '#F5F5F7'
NAV_MUTE = '#8E8E93'

PALETTE = [
    BLUE, ORANGE, GREEN, PURPLE, RED, TEAL,
    '#FF2D55', '#5856D6', '#FFCC00', '#A2845E',
    '#30B0C7', '#BF5AF2', '#FF6B00', '#30D158', '#0A84FF',
]


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'rgba({r},{g},{b},{alpha})'


def _chart(height=320):
    return dict(
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font=dict(family='Inter, -apple-system, sans-serif', color=TEXT, size=13),
        height=height,
        margin=dict(l=8, r=8, t=8, b=40),
        colorway=PALETTE,
        xaxis=dict(
            gridcolor='#EBEBF0', linecolor=SEP, zeroline=False, showgrid=True,
            tickfont=dict(color=MUTED, size=11), ticklen=0,
            title_font=dict(color=SECONDARY, size=12),
        ),
        yaxis=dict(
            gridcolor='#EBEBF0', linecolor=SEP, zeroline=False, showgrid=True,
            tickfont=dict(color=MUTED, size=11), ticklen=0,
            title_font=dict(color=SECONDARY, size=12),
        ),
        hoverlabel=dict(
            bgcolor=PANEL, bordercolor=SEP,
            font=dict(color=TEXT, size=13, family='Inter, sans-serif'),
        ),
        legend=dict(
            font=dict(color=SECONDARY, size=12),
            bgcolor='rgba(0,0,0,0)',
            orientation='h', yanchor='bottom', y=1.04, xanchor='right', x=1,
            itemsizing='constant', tracegroupgap=4,
        ),
    )


DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'ev_population.csv')

_raw = pd.read_csv(DATA_PATH, low_memory=False)
_raw.columns = [c.strip() for c in _raw.columns]
_raw = _raw.rename(columns={
    'Electric Vehicle Type': 'EV_Type_Full',
    'Electric Range':        'Range',
    'Model Year':            'Year',
    'Electric Utility':      'Utility',
})
_raw['Type']  = _raw['EV_Type_Full'].map({
    'Battery Electric Vehicle (BEV)':         'BEV',
    'Plug-in Hybrid Electric Vehicle (PHEV)': 'PHEV',
}).fillna('Other')
_raw['Make']  = _raw['Make'].str.strip().str.title()
_raw['Model'] = _raw['Model'].str.strip().str.title()

DF        = _raw[_raw['Year'].between(2015, 2025)].copy()
ALL_MAKES = ['All'] + sorted(DF['Make'].dropna().unique().tolist())
YEARS_WA  = sorted(DF['Year'].unique().tolist())

WA_COUNTIES = {
    'Adams':(46.97,-118.56),'Asotin':(46.34,-117.37),'Benton':(46.22,-119.39),
    'Chelan':(47.82,-120.62),'Clallam':(48.10,-123.80),'Clark':(45.79,-122.49),
    'Columbia':(46.31,-117.95),'Cowlitz':(46.20,-122.77),'Douglas':(47.63,-119.81),
    'Ferry':(48.60,-118.55),'Franklin':(46.55,-119.07),'Garfield':(46.43,-117.58),
    'Grant':(47.22,-119.45),'Grays Harbor':(47.14,-123.81),'Island':(48.23,-122.55),
    'Jefferson':(47.82,-124.10),'King':(47.49,-121.83),'Kitsap':(47.61,-122.65),
    'Kittitas':(47.12,-120.73),'Klickitat':(45.87,-120.75),'Lewis':(46.57,-122.42),
    'Lincoln':(47.58,-118.40),'Mason':(47.35,-123.22),'Okanogan':(48.55,-119.71),
    'Pacific':(46.57,-123.91),'Pend Oreille':(48.55,-117.43),'Pierce':(47.11,-122.09),
    'San Juan':(48.54,-122.96),'Skagit':(48.42,-121.76),'Skamania':(45.82,-121.93),
    'Snohomish':(48.04,-121.76),'Spokane':(47.62,-117.43),'Stevens':(48.35,-117.79),
    'Thurston':(46.97,-122.85),'Wahkiakum':(46.30,-123.43),'Walla Walla':(46.27,-118.37),
    'Whatcom':(48.84,-122.11),'Whitman':(46.90,-117.40),'Yakima':(46.65,-120.45),
}

GLOBAL_YEARS = list(range(2015, 2025))
GLOBAL_REGIONS = {
    'Asia-Pacific': ['China','Japan','South Korea','India'],
    'Europe':       ['Germany','Norway','UK','France','Netherlands','Sweden','Rest of EU'],
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
    Year         =[2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025],
    Cost_kWh     =[680, 540, 373, 295, 230, 185, 156, 137, 132, 138, 139, 115, 100],
    Avg_Range_km =[180, 195, 215, 240, 265, 290, 320, 355, 385, 415, 450, 490, 530],
)
df_battery = pd.DataFrame(BATTERY)

def _get_region(c):
    return next((r for r, cs in GLOBAL_REGIONS.items() if c in cs), 'Rest of World')

df_global = pd.DataFrame([
    dict(Year=y, Country=c, Region=_get_region(c), Total=v)
    for c, vs in GLOBAL_SALES.items()
    for y, v in zip(GLOBAL_YEARS, vs)
])


def _panel(children, flex=1, extra=None):
    s = {
        'background': PANEL,
        'borderRadius': '16px',
        'boxShadow': '0 2px 12px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04)',
        'overflow': 'hidden',
        'flex': str(flex),
        'minWidth': '0',
    }
    if extra:
        s.update(extra)
    return html.Div(children, style=s)


def _ph(title, subtitle=''):
    return html.Div([
        html.Div(title, style={
            'fontSize': '15px', 'fontWeight': '600', 'color': TEXT,
            'letterSpacing': '-0.2px', 'lineHeight': '1.3',
        }),
        html.Div(subtitle, style={
            'fontSize': '12px', 'color': SUBTLE, 'marginTop': '3px',
        }) if subtitle else '',
    ], style={'padding': '20px 20px 0'})


def _row(*children, gap='16px', mb='16px'):
    return html.Div(list(children),
                    style={'display': 'flex', 'gap': gap, 'marginBottom': mb,
                           'flexWrap': 'wrap', 'alignItems': 'stretch'},
                    className='ev-row')


def _legend_row(items):
    return html.Div([
        html.Div([
            html.Div(style={
                'width': '10px', 'height': '10px', 'borderRadius': '50%',
                'background': color, 'flexShrink': '0', 'marginTop': '2px',
            }),
            html.Div([
                html.Span(label, style={'fontSize': '12px', 'color': TEXT, 'fontWeight': '500'}),
                html.Span(f'  {pct}', style={'fontSize': '12px', 'color': SUBTLE}),
            ]),
        ], style={'display': 'flex', 'alignItems': 'flex-start', 'gap': '7px'})
        for color, label, pct in items
    ], style={
        'display': 'flex', 'gap': '18px', 'flexWrap': 'wrap',
        'padding': '12px 20px 18px',
    })


def _kpi(label, vid, did, accent=BLUE):
    return html.Div([
        html.Div(label, style={
            'fontSize': '11px', 'fontWeight': '600', 'color': SUBTLE,
            'textTransform': 'uppercase', 'letterSpacing': '0.8px',
        }),
        html.Div(id=vid, style={
            'fontSize': '2.1rem', 'fontWeight': '700', 'color': TEXT,
            'letterSpacing': '-1px', 'lineHeight': '1.1', 'marginTop': '10px',
            'fontVariantNumeric': 'tabular-nums',
        }),
        html.Div(id=did, style={
            'fontSize': '12px', 'color': MUTED, 'marginTop': '6px', 'fontWeight': '400',
        }),
        html.Div(style={
            'height': '3px', 'width': '28px', 'background': accent,
            'borderRadius': '2px', 'marginTop': '16px',
        }),
    ], style={
        'background': PANEL,
        'borderRadius': '16px',
        'boxShadow': '0 2px 12px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04)',
        'padding': '22px 24px',
        'flex': '1',
        'minWidth': '160px',
    })


def _pill_label(text):
    return html.Div(text, style={
        'fontSize': '10px', 'fontWeight': '600', 'color': SUBTLE,
        'textTransform': 'uppercase', 'letterSpacing': '0.8px', 'marginBottom': '6px',
    })


app = dash.Dash(__name__, suppress_callback_exceptions=True, title='EV Dashboard')
server = app.server

_yr_marks = {
    y: {'label': str(y), 'style': {'color': SUBTLE, 'fontSize': '10px'}}
    for y in YEARS_WA if y % 2 == 1
}

def _ts():
    return {
        'background': 'transparent', 'border': 'none',
        'borderBottom': '2px solid transparent',
        'color': NAV_MUTE, 'fontSize': '13px', 'fontWeight': '500',
        'padding': '13px 18px', 'fontFamily': 'Inter, sans-serif',
    }

def _tss():
    s = _ts()
    s.update({'color': NAV_TEXT, 'fontWeight': '600', 'borderBottom': f'2px solid {BLUE}'})
    return s


app.layout = html.Div([

    html.Div([
        html.Div([
            html.Span('EV', style={'fontWeight': '800', 'color': NAV_TEXT, 'fontSize': '14px',
                                   'letterSpacing': '-0.3px'}),
            html.Span('  Dashboard', style={'fontWeight': '400', 'color': NAV_MUTE, 'fontSize': '14px'}),
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

        html.Div('data.wa.gov · IEA', style={
            'fontSize': '11px', 'color': NAV_MUTE, 'whiteSpace': 'nowrap',
        }),
    ], style={
        'background': NAV_BG, 'padding': '0 32px',
        'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between',
        'position': 'sticky', 'top': '0', 'zIndex': '100', 'minHeight': '52px',
    }),

    html.Div([

        html.Div([
            html.H1('EV Market Intelligence', style={
                'fontSize': '28px', 'fontWeight': '700', 'color': TEXT,
                'letterSpacing': '-0.6px', 'margin': '0',
            }),
            html.P('Washington State Department of Licensing · 280,000+ registered vehicles',
                   style={'fontSize': '13px', 'color': MUTED, 'marginTop': '5px'}),
        ], style={'padding': '32px 32px 0'}),

        html.Div([
            html.Div([
                _pill_label('Model Year'),
                dcc.RangeSlider(
                    id='yr-slider', min=2015, max=2025, step=1, value=[2015, 2025],
                    marks=_yr_marks, allowCross=False,
                    tooltip={'placement': 'bottom', 'always_visible': False},
                ),
            ], style={'flex': '3', 'minWidth': '220px'}),
            html.Div(style={'width': '1px', 'background': SEP, 'alignSelf': 'stretch'}),
            html.Div([
                _pill_label('EV Type'),
                dcc.RadioItems(
                    id='type-filter', value='All', inline=True,
                    options=[{'label': '  All', 'value': 'All'},
                             {'label': '  BEV', 'value': 'BEV'},
                             {'label': '  PHEV', 'value': 'PHEV'}],
                    inputStyle={'marginRight': '4px'},
                    labelStyle={'marginRight': '18px', 'color': TEXT, 'fontSize': '13px', 'cursor': 'pointer'},
                ),
            ], style={'flex': '1'}),
            html.Div(style={'width': '1px', 'background': SEP, 'alignSelf': 'stretch'}),
            html.Div([
                _pill_label('Make'),
                dcc.Dropdown(
                    id='make-filter',
                    options=[{'label': m, 'value': m} for m in ALL_MAKES],
                    value='All', clearable=False, style={'minWidth': '150px'},
                ),
            ], style={'flex': '1.2'}),
        ], style={
            'display': 'flex', 'alignItems': 'center', 'gap': '24px',
            'background': PANEL,
            'borderRadius': '16px',
            'boxShadow': '0 2px 12px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04)',
            'padding': '16px 24px',
            'margin': '20px 32px 0',
            'flexWrap': 'wrap',
        }),

        html.Div([
            _kpi('Total Registered EVs',   'kpi-total', 'kpi-total-d', BLUE),
            _kpi('Battery Electric (BEV)', 'kpi-bev',   'kpi-bev-d',   GREEN),
            _kpi('Plug-in Hybrid (PHEV)',  'kpi-phev',  'kpi-phev-d',  ORANGE),
            _kpi('Market Leader',          'kpi-top',   'kpi-top-d',   PURPLE),
        ], style={'display': 'flex', 'gap': '16px', 'padding': '20px 32px 0', 'flexWrap': 'wrap'}),

        html.Div(id='tab-content'),

    ], style={'background': BG, 'minHeight': 'calc(100vh - 52px)'}),

    html.Div(
        'EV Market Dashboard  ·  Washington State DOL  ·  IEA Global EV Outlook  ·  Dash & Plotly',
        style={
            'textAlign': 'center', 'padding': '18px', 'color': SUBTLE,
            'fontSize': '11px', 'background': PANEL, 'borderTop': f'1px solid {SEP}',
        }),

], style={'fontFamily': 'Inter, -apple-system, sans-serif'})


@app.callback(Output('tab-content', 'children'), Input('main-tabs', 'value'))
def render_tab(tab):
    P = '20px 32px 32px'

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


def _filter(yr_range, ev_type, make):
    yr0, yr1 = yr_range
    d = DF[(DF['Year'] >= yr0) & (DF['Year'] <= yr1)]
    if ev_type != 'All':
        d = d[d['Type'] == ev_type]
    if make != 'All':
        d = d[d['Make'] == make]
    return d


def _bar_h(x_vals, y_vals, color, hover_tmpl):
    n = len(y_vals)
    threshold = max(n - 3, 0)
    colors = [color if i >= threshold else _rgba(color, 0.38) for i in range(n)]
    return go.Bar(
        x=x_vals, y=y_vals, orientation='h',
        marker=dict(color=colors, line=dict(color='rgba(0,0,0,0)', width=0)),
        hovertemplate=hover_tmpl,
    )


@app.callback(
    Output('kpi-total',  'children'), Output('kpi-total-d', 'children'),
    Output('kpi-bev',    'children'), Output('kpi-bev-d',   'children'),
    Output('kpi-phev',   'children'), Output('kpi-phev-d',  'children'),
    Output('kpi-top',    'children'), Output('kpi-top-d',   'children'),
    Input('yr-slider', 'value'), Input('type-filter', 'value'), Input('make-filter', 'value'),
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
    sign  = lambda v: ('↑ ' if v >= 0 else '↓ ') + f'{abs(v):.1f}%'
    col   = lambda v: {'color': GREEN if v >= 0 else RED, 'fontSize': '12px'}
    return (
        f'{total:,}',
        html.Span(sign(delta) + f'  vs {yr0}–{max(yr0, yr1-1)}', style=col(delta)),
        f'{bev:,}',
        html.Span(f'{bev/total*100:.1f}% of fleet' if total else '—',
                  style={'color': MUTED, 'fontSize': '12px'}),
        f'{phev:,}',
        html.Span(f'{phev/total*100:.1f}% of fleet' if total else '—',
                  style={'color': MUTED, 'fontSize': '12px'}),
        top_make,
        html.Span(f'{top_share:.1f}% share', style={'color': MUTED, 'fontSize': '12px'}),
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
    fig3 = go.Figure(_bar_h(mc.Count, mc.Make, BLUE,
                            '<b>%{y}</b>: %{x:,}<extra></extra>'))
    fig3.update_layout(**_chart(height=300), showlegend=False)
    fig3.update_layout(margin=dict(l=110, r=12, t=8, b=36))

    model_ct = d['Model'].value_counts().head(15).reset_index()
    model_ct.columns = ['Model', 'Count']
    model_ct = model_ct.sort_values('Count')
    fig4 = go.Figure(_bar_h(model_ct.Count, model_ct.Model, GREEN,
                            '<b>%{y}</b>: %{x:,}<extra></extra>'))
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
    fig4  = go.Figure(_bar_h(rng.values, rng.index, TEAL,
                             '<b>%{y}</b>: %{x:.0f} mi<extra></extra>'))
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
    fig2 = go.Figure(_bar_h(top_c.Count, top_c.County, BLUE,
                            '<b>%{y}</b>: %{x:,}<extra></extra>'))
    fig2.update_layout(**_chart(height=380), showlegend=False)
    fig2.update_layout(margin=dict(l=102, r=12, t=8, b=36))

    city_ct = d['City'].value_counts().head(20).reset_index()
    city_ct.columns = ['City', 'Count']
    city_ct = city_ct.sort_values('Count')
    fig3 = go.Figure(_bar_h(city_ct.Count, city_ct.City, GREEN,
                            '<b>%{y}</b>: %{x:,}<extra></extra>'))
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


if __name__ == '__main__':
    app.run(debug=True, port=8050)
