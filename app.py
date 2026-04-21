"""
EV Energy Sector Dashboard
Real data: Washington State EV Population (data.wa.gov) — 280,000+ registrations
Global context data calibrated to IEA Global EV Outlook 2015-2024
"""

import os
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ══════════════════════════════════════════════════════════════════════════════
# THEME
# ══════════════════════════════════════════════════════════════════════════════

BG     = '#0d1117'
CARD   = '#161b22'
CARD2  = '#1c2333'
BORDER = '#30363d'
TEXT   = '#e6edf3'
MUTED  = '#8b949e'

GREEN  = '#3fb950';  BLUE   = '#58a6ff';  AMBER  = '#d29922'
PURPLE = '#bc8cff';  TEAL   = '#39d353';  RED    = '#f85149'
ORANGE = '#ffa657';  CYAN   = '#79c0ff';  LIME   = '#7ee787'
ROSE   = '#ff7b72';  INDIGO = '#a5d6ff'

PALETTE = [GREEN, BLUE, AMBER, PURPLE, TEAL, RED, ORANGE, CYAN, LIME, ROSE, INDIGO,
           '#e879f9', '#f0abfc', '#67e8f9', '#bef264']

def _layout(height=320, legend_h=True, margins=None):
    m = margins or dict(l=10, r=10, t=28, b=30)
    leg = dict(bgcolor='rgba(0,0,0,0)', font=dict(color=MUTED, size=11),
               orientation='h', yanchor='bottom', y=1.01, xanchor='right', x=1)
    if not legend_h:
        leg = dict(bgcolor='rgba(0,0,0,0)', font=dict(color=MUTED, size=11))
    return dict(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color=TEXT, size=12),
        height=height, margin=m, legend=leg, colorway=PALETTE,
        xaxis=dict(gridcolor='#1f2937', linecolor=BORDER, tickcolor=MUTED,
                   tickfont=dict(color=MUTED, size=11), zeroline=False),
        yaxis=dict(gridcolor='#1f2937', linecolor=BORDER, tickcolor=MUTED,
                   tickfont=dict(color=MUTED, size=11), zeroline=False),
        hoverlabel=dict(bgcolor=CARD2, bordercolor=BORDER, font=dict(color=TEXT, size=12)),
    )

# ══════════════════════════════════════════════════════════════════════════════
# DATA LOAD & PREP
# ══════════════════════════════════════════════════════════════════════════════

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'ev_population.csv')

_raw = pd.read_csv(DATA_PATH, low_memory=False)
_raw.columns = [c.strip() for c in _raw.columns]

_raw = _raw.rename(columns={
    'VIN (1-10)': 'VIN', 'Electric Vehicle Type': 'EV_Type_Full',
    'Electric Range': 'Range', 'Model Year': 'Year',
    'Vehicle Location': 'Location', 'Electric Utility': 'Utility',
    'Postal Code': 'ZIP', 'Legislative District': 'District',
    'Clean Alternative Fuel Vehicle (CAFV) Eligibility': 'CAFV',
})

_raw['Type'] = _raw['EV_Type_Full'].map({
    'Battery Electric Vehicle (BEV)': 'BEV',
    'Plug-in Hybrid Electric Vehicle (PHEV)': 'PHEV',
}).fillna('Other')

_raw['Make'] = _raw['Make'].str.strip().str.title()
_raw['Model'] = _raw['Model'].str.strip().str.title()

# Filter to years with meaningful data
DF = _raw[_raw['Year'].between(2015, 2025)].copy()
DF_ALL = _raw.copy()  # for range analysis (include older EVs)

ALL_MAKES = ['All'] + sorted(DF['Make'].dropna().unique().tolist())
YEARS_WA  = sorted(DF['Year'].unique().tolist())

# WA County centroids
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

# ── Global context data (IEA-calibrated) ─────────────────────────────────────

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
    Energy_Density=[150,160, 175, 185, 200, 215, 235, 255, 275, 295, 315, 340, 360],
    Avg_Range_km =[180, 195, 215, 240, 265, 290, 320, 355, 385, 415, 450, 490, 530],
)
df_battery = pd.DataFrame(BATTERY)

def _get_region(c):
    return next((r for r,cs in GLOBAL_REGIONS.items() if c in cs), 'Rest of World')

_g = [dict(Year=y, Country=c, Region=_get_region(c), Total=v)
      for c, vs in GLOBAL_SALES.items() for y, v in zip(GLOBAL_YEARS, vs)]
df_global = pd.DataFrame(_g)

# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _card(children, style=None):
    s = {'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'4px 4px 0'}
    if style: s.update(style)
    return html.Div(children, style=s)

def _title(t, sub=''):
    return html.Div([
        html.Div(t, style={'fontSize':'13px','fontWeight':'600','color':TEXT,
                           'padding':'12px 16px 0','letterSpacing':'0.2px'}),
        html.Div(sub, style={'fontSize':'11px','color':MUTED,'padding':'1px 16px 4px'}) if sub else '',
    ])

def _kpi(icon, label, vid, color=GREEN, did=None):
    return html.Div([
        html.Div([html.Span(icon, style={'fontSize':'20px'}),
                  html.Div(label, style={'fontSize':'10px','color':MUTED,'marginTop':'3px',
                                         'textTransform':'uppercase','letterSpacing':'0.6px','fontWeight':'600'})],
                 style={'display':'flex','alignItems':'center','gap':'9px'}),
        html.H2(id=vid, style={'fontSize':'1.8rem','fontWeight':'700','color':color,
                               'margin':'6px 0 1px','lineHeight':'1'}),
        html.Div(id=did, style={'fontSize':'11px','fontWeight':'500','color':MUTED}) if did else '',
    ], style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px',
              'padding':'16px 20px','flex':'1','minWidth':'170px'})

def _row(*children, gap='16px', mb='16px'):
    return html.Div(list(children), style={'display':'flex','gap':gap,'marginBottom':mb,'flexWrap':'wrap'})

def _tab_style(sel=False):
    base = {'background':CARD,'border':f'1px solid {BORDER}','borderBottom':'none',
            'borderRadius':'8px 8px 0 0','fontSize':'13px','fontWeight':'500',
            'padding':'9px 16px','marginRight':'4px','color':MUTED}
    if sel:
        base.update({'background':CARD2,'borderColor':BLUE,'color':BLUE,'fontWeight':'600'})
    return base

def _tab_content(children):
    return html.Div(children, style={'background':BG,'border':f'1px solid {BORDER}',
                                     'borderRadius':'0 8px 8px 8px','padding':'18px'})

# ══════════════════════════════════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════════════════════════════════

app = dash.Dash(__name__, suppress_callback_exceptions=True, title='EV Energy Dashboard')
server = app.server  # for gunicorn

_yr_marks = {y: {'label':str(y),'style':{'color':MUTED,'fontSize':'10px'}}
             for y in YEARS_WA if y % 2 == 1}

app.layout = html.Div([

    # ── Header ────────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Span('⚡', style={'fontSize':'26px'}),
            html.Div([
                html.H1('EV Energy Dashboard',
                        style={'fontSize':'17px','fontWeight':'700','color':TEXT,'margin':'0'}),
                html.Div('Washington State · 280,000+ Real EV Registrations + Global IEA Context',
                         style={'fontSize':'11px','color':MUTED,'marginTop':'2px'}),
            ]),
        ], style={'display':'flex','alignItems':'center','gap':'11px'}),
        html.Div([
            html.Span('REAL DATA', style={
                'background':'linear-gradient(90deg,#238636,#2ea043)',
                'color':'#fff','fontSize':'10px','fontWeight':'700',
                'padding':'3px 9px','borderRadius':'20px','letterSpacing':'0.5px'}),
            html.Span('Source: data.wa.gov | IEA EV Outlook',
                      style={'color':MUTED,'fontSize':'11px','marginLeft':'10px'}),
        ], style={'display':'flex','alignItems':'center'}),
    ], style={
        'background':'linear-gradient(135deg,#0d1117 0%,#161b22 60%,#1c2333 100%)',
        'borderBottom':f'1px solid {BORDER}','padding':'14px 32px',
        'display':'flex','alignItems':'center','justifyContent':'space-between',
        'position':'sticky','top':'0','zIndex':'100',
    }),

    # ── KPI Row ───────────────────────────────────────────────────────────────
    html.Div([
        _kpi('🚗','Total EVs Registered', 'kpi-total', GREEN,  'kpi-total-d'),
        _kpi('⚡','Battery EVs (BEV)',     'kpi-bev',   BLUE,   'kpi-bev-d'),
        _kpi('🔌','Plug-in Hybrids (PHEV)','kpi-phev',  AMBER,  'kpi-phev-d'),
        _kpi('🏆','Market Leader',         'kpi-top',   PURPLE, 'kpi-top-d'),
    ], style={'display':'flex','gap':'14px','padding':'20px 32px 0','flexWrap':'wrap'}),

    # ── Filters ───────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Div('Model Year', style={'fontSize':'10px','color':MUTED,'fontWeight':'600',
                                           'textTransform':'uppercase','letterSpacing':'0.6px','marginBottom':'8px'}),
            dcc.RangeSlider(id='yr-slider', min=2015, max=2025, step=1, value=[2015,2025],
                            marks=_yr_marks, allowCross=False,
                            tooltip={'placement':'bottom','always_visible':False}),
        ], style={'flex':'3','minWidth':'260px'}),
        html.Div([
            html.Div('EV Type', style={'fontSize':'10px','color':MUTED,'fontWeight':'600',
                                        'textTransform':'uppercase','letterSpacing':'0.6px','marginBottom':'6px'}),
            dcc.RadioItems(id='type-filter', value='All', inline=True,
                           options=[{'label':' All','value':'All'},
                                    {'label':' BEV','value':'BEV'},
                                    {'label':' PHEV','value':'PHEV'}],
                           inputStyle={'marginRight':'4px'},
                           labelStyle={'marginRight':'14px','color':MUTED,'fontSize':'13px'}),
        ], style={'flex':'1'}),
        html.Div([
            html.Div('Make', style={'fontSize':'10px','color':MUTED,'fontWeight':'600',
                                     'textTransform':'uppercase','letterSpacing':'0.6px','marginBottom':'6px'}),
            dcc.Dropdown(id='make-filter', options=[{'label':m,'value':m} for m in ALL_MAKES],
                         value='All', clearable=False,
                         style={'background':CARD2,'border':f'1px solid {BORDER}',
                                'color':TEXT,'minWidth':'160px'}),
        ], style={'flex':'1.2'}),
    ], style={
        'display':'flex','alignItems':'center','gap':'28px','padding':'14px 26px',
        'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px',
        'margin':'18px 32px 0','flexWrap':'wrap',
    }),

    # ── Tabs ──────────────────────────────────────────────────────────────────
    html.Div([
        dcc.Tabs(id='main-tabs', value='overview', children=[

            # ─── Tab 1: Fleet Overview ──────────────────────────────────────
            dcc.Tab(label='📊  Fleet Overview', value='overview',
                    style=_tab_style(), selected_style=_tab_style(True),
                    children=_tab_content([
                        _row(
                            _card([_title('Registrations by Model Year','Annual EV fleet growth'),
                                   dcc.Graph(id='ov-year-bar', config={'displayModeBar':False})], {'flex':'2'}),
                            _card([_title('BEV vs PHEV Split','Battery vs Plug-in Hybrid'),
                                   dcc.Graph(id='ov-type-pie', config={'displayModeBar':False})], {'flex':'1'}),
                        ),
                        _row(
                            _card([_title('Top 15 Makes','By registered vehicle count'),
                                   dcc.Graph(id='ov-make-bar', config={'displayModeBar':False})], {'flex':'1'}),
                            _card([_title('Top 15 Models','Most popular EV models'),
                                   dcc.Graph(id='ov-model-bar', config={'displayModeBar':False})], {'flex':'1'}),
                        ),
                    ])),

            # ─── Tab 2: Manufacturers ───────────────────────────────────────
            dcc.Tab(label='🏭  Manufacturers', value='mfr',
                    style=_tab_style(), selected_style=_tab_style(True),
                    children=_tab_content([
                        _row(
                            _card([_title('Market Share','% of total registrations'),
                                   dcc.Graph(id='mf-pie', config={'displayModeBar':False})], {'flex':'1.2'}),
                            _card([_title('BEV vs PHEV by Make','Top 12 manufacturers'),
                                   dcc.Graph(id='mf-type-bar', config={'displayModeBar':False})], {'flex':'2'}),
                        ),
                        _row(
                            _card([_title('Make Popularity Over Years','Registration count by model year'),
                                   dcc.Graph(id='mf-trend', config={'displayModeBar':False})], {'flex':'2'}),
                            _card([_title('Average Electric Range by Make','Miles · BEV only'),
                                   dcc.Graph(id='mf-range', config={'displayModeBar':False})], {'flex':'1'}),
                        ),
                    ])),

            # ─── Tab 3: Models & Range ──────────────────────────────────────
            dcc.Tab(label='🔋  Models & Range', value='models',
                    style=_tab_style(), selected_style=_tab_style(True),
                    children=_tab_content([
                        _row(
                            _card([_title('Electric Range Distribution','Miles · BEVs only'),
                                   dcc.Graph(id='md-hist', config={'displayModeBar':False})], {'flex':'2'}),
                            _card([_title('Avg Range by Model Year','BEV fleet progress'),
                                   dcc.Graph(id='md-range-year', config={'displayModeBar':False})], {'flex':'1'}),
                        ),
                        _row(
                            _card([_title('Top 20 Models by Electric Range','Maximum rated range · miles'),
                                   dcc.Graph(id='md-top-range', config={'displayModeBar':False})], {'flex':'1'}),
                            _card([_title('Model Volume vs Avg Range','Bubble = registration count'),
                                   dcc.Graph(id='md-scatter', config={'displayModeBar':False})], {'flex':'1'}),
                        ),
                    ])),

            # ─── Tab 4: Geography ───────────────────────────────────────────
            dcc.Tab(label='🗺️  Geography', value='geo',
                    style=_tab_style(), selected_style=_tab_style(True),
                    children=_tab_content([
                        _row(
                            _card([_title('EV Registrations by County','Bubble size = count'),
                                   dcc.Graph(id='geo-map', config={'displayModeBar':False})],
                                  {'flex':'2'}),
                            _card([_title('Top 15 Counties','Registered EVs'),
                                   dcc.Graph(id='geo-county', config={'displayModeBar':False})],
                                  {'flex':'1'}),
                        ),
                        _row(
                            _card([_title('Top 20 Cities','Registered EVs'),
                                   dcc.Graph(id='geo-city', config={'displayModeBar':False})], {'flex':'1'}),
                            _card([_title('Electric Utility Distribution','Which grid powers WA EVs'),
                                   dcc.Graph(id='geo-utility', config={'displayModeBar':False})], {'flex':'1'}),
                        ),
                    ])),

            # ─── Tab 5: Global Context ──────────────────────────────────────
            dcc.Tab(label='🌍  Global Context', value='global',
                    style=_tab_style(), selected_style=_tab_style(True),
                    children=_tab_content([
                        _row(
                            _card([_title('Global EV Sales by Region 2015–2024','Million units · IEA data'),
                                   dcc.Graph(id='gl-sales', config={'displayModeBar':False})], {'flex':'2'}),
                            _card([_title('Battery Pack Cost Trend','$/kWh · BloombergNEF'),
                                   dcc.Graph(id='gl-battery', config={'displayModeBar':False})], {'flex':'1'}),
                        ),
                        _row(
                            _card([_title('Top Countries – Annual EV Sales','Millions of units'),
                                   dcc.Graph(id='gl-countries', config={'displayModeBar':False})], {'flex':'1'}),
                            _card([_title('WA State vs Global','WA % of US EV market & avg range vs global avg'),
                                   dcc.Graph(id='gl-wa-vs-global', config={'displayModeBar':False})], {'flex':'1'}),
                        ),
                    ])),

        ], colors={'border':BORDER,'primary':BLUE,'background':BG}),
    ], style={'margin':'0 32px'}),

    # ── Footer ────────────────────────────────────────────────────────────────
    html.Div('⚡ EV Energy Dashboard · Washington State DOL + IEA Global EV Outlook · Built with Dash & Plotly',
             style={'textAlign':'center','padding':'18px','color':MUTED,'fontSize':'11px',
                    'marginTop':'20px','borderTop':f'1px solid {BORDER}'}),

], style={'backgroundColor':BG,'minHeight':'100vh','fontFamily':'Inter, sans-serif'})


# ══════════════════════════════════════════════════════════════════════════════
# SHARED FILTER HELPER
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
# CALLBACKS — KPIs
# ══════════════════════════════════════════════════════════════════════════════

@app.callback(
    Output('kpi-total','children'), Output('kpi-total-d','children'),
    Output('kpi-bev',  'children'), Output('kpi-bev-d',  'children'),
    Output('kpi-phev', 'children'), Output('kpi-phev-d', 'children'),
    Output('kpi-top',  'children'), Output('kpi-top-d',  'children'),
    Input('yr-slider',   'value'),
    Input('type-filter', 'value'),
    Input('make-filter', 'value'),
)
def update_kpis(yr_range, ev_type, make):
    d = _filter(yr_range, ev_type, make)
    total = len(d)
    bev   = (d['Type'] == 'BEV').sum()
    phev  = (d['Type'] == 'PHEV').sum()

    # prev year comparison
    yr0, yr1 = yr_range
    d_prev = _filter([yr0, max(yr0, yr1-1)], ev_type, make)
    t_prev = len(d_prev) if yr1 > yr0 else total
    delta  = ((total - t_prev) / t_prev * 100) if t_prev else 0

    top_make  = d['Make'].value_counts().index[0] if total else 'N/A'
    top_share = d['Make'].value_counts().iloc[0] / total * 100 if total else 0

    arrow = lambda v: ('▲ ' if v >= 0 else '▼ ') + f'{abs(v):.1f}%'
    g = lambda v: {'color': GREEN if v >= 0 else RED}

    return (
        f'{total:,}',
        html.Span(arrow(delta) + f' vs {yr0}–{max(yr0,yr1-1)}', style=g(delta)),
        f'{bev:,}',
        html.Span(f'{bev/total*100:.1f}% of fleet' if total else '—', style={'color': MUTED}),
        f'{phev:,}',
        html.Span(f'{phev/total*100:.1f}% of fleet' if total else '—', style={'color': MUTED}),
        top_make,
        html.Span(f'{top_share:.1f}% share', style={'color': MUTED}),
    )


# ══════════════════════════════════════════════════════════════════════════════
# CALLBACKS — Tab 1: Fleet Overview
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
def tab_overview(yr_range, ev_type, make):
    d = _filter(yr_range, ev_type, make)

    # 1. Registrations by year, split BEV / PHEV
    yr_type = d.groupby(['Year','Type']).size().reset_index(name='Count')
    fig1 = go.Figure()
    for t, color in [('BEV', BLUE), ('PHEV', AMBER)]:
        sub = yr_type[yr_type.Type == t]
        fig1.add_trace(go.Bar(
            x=sub.Year, y=sub.Count, name=t,
            marker=dict(color=color, opacity=0.85),
            hovertemplate='<b>%{x} %{fullData.name}</b>: %{y:,}<extra></extra>',
        ))
    fig1.update_layout(**_layout(height=290), barmode='stack')
    fig1.update_layout(yaxis_title='Registrations')

    # 2. BEV vs PHEV donut
    type_counts = d['Type'].value_counts()
    fig2 = go.Figure(go.Pie(
        labels=type_counts.index, values=type_counts.values, hole=0.55,
        marker=dict(colors=[BLUE, AMBER], line=dict(color=BG, width=2)),
        textinfo='label+percent', textfont=dict(size=11, color=TEXT),
        hovertemplate='<b>%{label}</b>: %{value:,} (%{percent})<extra></extra>',
    ))
    fig2.update_layout(**_layout(height=290), showlegend=False)
    fig2.update_layout(
        annotations=[dict(text=f'{len(d):,}', x=0.5, y=0.5,
                          font=dict(size=15, color=TEXT, family='Inter'), showarrow=False)],
        margin=dict(l=10,r=10,t=20,b=10),
    )

    # 3. Top 15 makes
    make_ct = d['Make'].value_counts().head(15).reset_index()
    make_ct.columns = ['Make','Count']
    make_ct = make_ct.sort_values('Count')
    fig3 = go.Figure(go.Bar(
        x=make_ct.Count, y=make_ct.Make, orientation='h',
        marker=dict(color=PALETTE[:len(make_ct)], opacity=0.85),
        hovertemplate='<b>%{y}</b>: %{x:,}<extra></extra>',
    ))
    fig3.update_layout(**_layout(height=290), showlegend=False)
    fig3.update_layout(margin=dict(l=110,r=10,t=20,b=30))

    # 4. Top 15 models
    model_ct = d['Model'].value_counts().head(15).reset_index()
    model_ct.columns = ['Model','Count']
    model_ct = model_ct.sort_values('Count')
    fig4 = go.Figure(go.Bar(
        x=model_ct.Count, y=model_ct.Model, orientation='h',
        marker=dict(color=[GREEN if i >= 12 else f'{GREEN}77' for i in range(len(model_ct))],
                    opacity=0.85),
        hovertemplate='<b>%{y}</b>: %{x:,}<extra></extra>',
    ))
    fig4.update_layout(**_layout(height=290), showlegend=False)
    fig4.update_layout(margin=dict(l=130,r=10,t=20,b=30))

    return fig1, fig2, fig3, fig4


# ══════════════════════════════════════════════════════════════════════════════
# CALLBACKS — Tab 2: Manufacturers
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
def tab_manufacturers(yr_range, ev_type, make):
    d = _filter(yr_range, ev_type, make)

    # 1. Market share donut (top 10 + others)
    mc = d['Make'].value_counts()
    top10 = mc.head(10)
    other = mc.iloc[10:].sum()
    labels = list(top10.index) + (['Others'] if other > 0 else [])
    values = list(top10.values) + ([other] if other > 0 else [])
    fig1 = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.5,
        marker=dict(colors=PALETTE[:len(labels)], line=dict(color=BG, width=2)),
        textinfo='label+percent', textfont=dict(size=10, color=TEXT),
        hovertemplate='<b>%{label}</b>: %{value:,} (%{percent})<extra></extra>',
        insidetextorientation='radial',
    ))
    fig1.update_layout(**_layout(height=320), showlegend=False)
    fig1.update_layout(margin=dict(l=10,r=10,t=20,b=10))

    # 2. BEV vs PHEV by make (top 12)
    top12 = mc.head(12).index.tolist()
    sub = d[d['Make'].isin(top12)]
    mt = sub.groupby(['Make','Type']).size().reset_index(name='Count')
    mt_bev  = mt[mt.Type=='BEV']
    mt_phev = mt[mt.Type=='PHEV']
    order = top12[::-1]
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name='BEV', y=[m for m in order],
                          x=[mt_bev[mt_bev.Make==m]['Count'].sum() for m in order],
                          orientation='h', marker=dict(color=BLUE, opacity=0.85),
                          hovertemplate='BEV <b>%{y}</b>: %{x:,}<extra></extra>'))
    fig2.add_trace(go.Bar(name='PHEV', y=[m for m in order],
                          x=[mt_phev[mt_phev.Make==m]['Count'].sum() for m in order],
                          orientation='h', marker=dict(color=AMBER, opacity=0.85),
                          hovertemplate='PHEV <b>%{y}</b>: %{x:,}<extra></extra>'))
    fig2.update_layout(**_layout(height=320), barmode='stack')
    fig2.update_layout(margin=dict(l=110,r=10,t=28,b=30))

    # 3. Top 6 makes trend by year
    top6 = mc.head(6).index.tolist()
    sub6 = d[d['Make'].isin(top6)]
    trend = sub6.groupby(['Year','Make']).size().reset_index(name='Count')
    fig3 = go.Figure()
    for i, mk in enumerate(top6):
        s = trend[trend.Make == mk]
        fig3.add_trace(go.Scatter(
            x=s.Year, y=s.Count, name=mk, mode='lines+markers',
            line=dict(color=PALETTE[i], width=2.5),
            marker=dict(size=5),
            hovertemplate=f'<b>{mk}</b> %{{x}}: %{{y:,}}<extra></extra>',
        ))
    fig3.update_layout(**_layout(height=320))
    fig3.update_layout(yaxis_title='Registrations', hovermode='x unified')

    # 4. Avg range by make (BEV only)
    bev_d = d[(d['Type']=='BEV') & (d['Range']>0)]
    rng = bev_d.groupby('Make')['Range'].mean().sort_values(ascending=False).head(15)
    rng = rng.sort_values()
    fig4 = go.Figure(go.Bar(
        x=rng.values, y=rng.index, orientation='h',
        marker=dict(color=[GREEN if v >= rng.median() else f'{GREEN}66' for v in rng.values]),
        hovertemplate='<b>%{y}</b>: %{x:.0f} mi<extra></extra>',
    ))
    fig4.update_layout(**_layout(height=320), showlegend=False)
    fig4.update_layout(xaxis_title='Avg Range (miles)', margin=dict(l=120,r=10,t=20,b=30))

    return fig1, fig2, fig3, fig4


# ══════════════════════════════════════════════════════════════════════════════
# CALLBACKS — Tab 3: Models & Range
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
def tab_models(yr_range, ev_type, make):
    d = _filter(yr_range, ev_type, make)
    bev = d[(d['Type']=='BEV') & (d['Range']>0)]

    # 1. Range histogram
    fig1 = go.Figure(go.Histogram(
        x=bev['Range'], nbinsx=40,
        marker=dict(color=BLUE, opacity=0.8, line=dict(color=BG, width=0.5)),
        hovertemplate='Range %{x} mi: %{y:,} vehicles<extra></extra>',
    ))
    fig1.update_layout(**_layout(height=290), showlegend=False)
    fig1.update_layout(xaxis_title='Electric Range (miles)', yaxis_title='Count')
    fig1.add_vline(x=bev['Range'].median(), line=dict(color=GREEN, dash='dash', width=1.5),
                   annotation_text=f'Median: {bev["Range"].median():.0f} mi',
                   annotation_font_color=GREEN, annotation_position='top right')

    # 2. Avg range by year
    ry = bev.groupby('Year')['Range'].agg(['mean','median']).reset_index()
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=ry.Year, y=ry['mean'], name='Mean',
                              mode='lines+markers', line=dict(color=GREEN, width=2.5),
                              marker=dict(size=6), hovertemplate='Mean %{x}: %{y:.0f} mi<extra></extra>'))
    fig2.add_trace(go.Scatter(x=ry.Year, y=ry['median'], name='Median',
                              mode='lines+markers', line=dict(color=BLUE, width=2, dash='dot'),
                              marker=dict(size=6), hovertemplate='Median %{x}: %{y:.0f} mi<extra></extra>'))
    fig2.update_layout(**_layout(height=290))
    fig2.update_layout(yaxis_title='Range (miles)', hovermode='x unified')

    # 3. Top 20 models by max range
    top_range = (bev.groupby('Model')['Range'].max()
                 .sort_values(ascending=False).head(20).reset_index().sort_values('Range'))
    fig3 = go.Figure(go.Bar(
        x=top_range.Range, y=top_range.Model, orientation='h',
        marker=dict(color=PALETTE[:len(top_range)], opacity=0.85),
        hovertemplate='<b>%{y}</b>: %{x:.0f} mi<extra></extra>',
    ))
    fig3.update_layout(**_layout(height=290), showlegend=False)
    fig3.update_layout(xaxis_title='Max Rated Range (miles)', margin=dict(l=140,r=10,t=20,b=30))

    # 4. Scatter: count vs avg range for top 30 models
    scatter_d = bev.groupby('Model').agg(Count=('Range','count'), Avg_Range=('Range','mean')).reset_index()
    scatter_d = scatter_d[scatter_d.Count >= 50].nlargest(30, 'Count')
    fig4 = go.Figure(go.Scatter(
        x=scatter_d.Avg_Range, y=scatter_d.Count,
        mode='markers+text',
        text=scatter_d.Model,
        textfont=dict(size=9, color=MUTED),
        textposition='top center',
        marker=dict(
            size=np.sqrt(scatter_d.Count / scatter_d.Count.max() * 2000) + 8,
            color=scatter_d.Avg_Range, colorscale='viridis',
            showscale=True,
            colorbar=dict(title='Range', tickfont=dict(color=MUTED,size=10),
                          bgcolor='rgba(0,0,0,0)', thickness=8, len=0.6),
            opacity=0.75, line=dict(color=BG, width=1),
        ),
        hovertemplate='<b>%{text}</b><br>Avg: %{x:.0f} mi | Count: %{y:,}<extra></extra>',
    ))
    fig4.update_layout(**_layout(height=290), showlegend=False)
    fig4.update_layout(xaxis_title='Avg Range (miles)', yaxis_title='Registrations')

    return fig1, fig2, fig3, fig4


# ══════════════════════════════════════════════════════════════════════════════
# CALLBACKS — Tab 4: Geography
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
def tab_geography(yr_range, ev_type, make):
    d = _filter(yr_range, ev_type, make)

    # 1. County bubble map
    county_ct = d['County'].value_counts().reset_index()
    county_ct.columns = ['County','Count']
    county_ct['lat'] = county_ct['County'].map(lambda c: WA_COUNTIES.get(c, (None,None))[0])
    county_ct['lon'] = county_ct['County'].map(lambda c: WA_COUNTIES.get(c, (None,None))[1])
    county_ct = county_ct.dropna(subset=['lat','lon'])

    fig1 = go.Figure(go.Scattergeo(
        lat=county_ct.lat, lon=county_ct.lon,
        text=county_ct.County,
        customdata=county_ct.Count,
        mode='markers+text', textfont=dict(size=9, color=TEXT),
        textposition='top center',
        marker=dict(
            size=np.sqrt(county_ct.Count / county_ct.Count.max()) * 45 + 6,
            color=county_ct.Count, colorscale=[[0,'#1f6feb'],[0.5,GREEN],[1.0,'#a7f3d0']],
            opacity=0.75, line=dict(color=BG, width=0.5),
            showscale=True,
            colorbar=dict(title='EVs', tickfont=dict(color=MUTED,size=10),
                          bgcolor='rgba(0,0,0,0)', thickness=8, len=0.6),
        ),
        hovertemplate='<b>%{text} County</b><br>EVs: %{customdata:,}<extra></extra>',
    ))
    fig1.update_layout(**_layout(height=340))
    fig1.update_layout(
        geo=dict(bgcolor='rgba(0,0,0,0)', showframe=False, showcoastlines=True,
                 coastlinecolor=BORDER, showland=True, landcolor='#1c2333',
                 showocean=True, oceancolor='#0d1117',
                 showlakes=True, lakecolor='#0d1117',
                 lonaxis=dict(range=[-125, -116]),
                 lataxis=dict(range=[45.5, 49.5]),
                 projection_type='mercator'),
        margin=dict(l=0,r=0,t=10,b=0),
    )

    # 2. Top 15 counties bar
    top_c = county_ct.nlargest(15,'Count').sort_values('Count')
    fig2 = go.Figure(go.Bar(
        x=top_c.Count, y=top_c.County, orientation='h',
        marker=dict(color=PALETTE[:len(top_c)], opacity=0.85),
        hovertemplate='<b>%{y}</b>: %{x:,}<extra></extra>',
    ))
    fig2.update_layout(**_layout(height=340), showlegend=False)
    fig2.update_layout(margin=dict(l=100,r=10,t=20,b=30))

    # 3. Top 20 cities
    city_ct = d['City'].value_counts().head(20).reset_index()
    city_ct.columns = ['City','Count']
    city_ct = city_ct.sort_values('Count')
    fig3 = go.Figure(go.Bar(
        x=city_ct.Count, y=city_ct.City, orientation='h',
        marker=dict(color=[GREEN if i >= 17 else f'{GREEN}66' for i in range(len(city_ct))]),
        hovertemplate='<b>%{y}</b>: %{x:,}<extra></extra>',
    ))
    fig3.update_layout(**_layout(height=340), showlegend=False)
    fig3.update_layout(margin=dict(l=110,r=10,t=20,b=30))

    # 4. Electric utility donut
    # Clean utility names (strip pipe-separated extras)
    util_clean = d['Utility'].dropna().str.split('||').str[0].str.strip()
    util_ct = util_clean.value_counts().head(8)
    other_u = util_clean.value_counts().iloc[8:].sum()
    u_labels = list(util_ct.index) + (['Others'] if other_u > 0 else [])
    u_values = list(util_ct.values) + ([other_u] if other_u > 0 else [])
    fig4 = go.Figure(go.Pie(
        labels=u_labels, values=u_values, hole=0.45,
        marker=dict(colors=PALETTE[:len(u_labels)], line=dict(color=BG, width=2)),
        textinfo='label+percent', textfont=dict(size=9, color=TEXT),
        hovertemplate='<b>%{label}</b>: %{value:,} (%{percent})<extra></extra>',
    ))
    fig4.update_layout(**_layout(height=340), showlegend=False)
    fig4.update_layout(margin=dict(l=10,r=10,t=20,b=10))

    return fig1, fig2, fig3, fig4


# ══════════════════════════════════════════════════════════════════════════════
# CALLBACKS — Tab 5: Global Context
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
def tab_global(yr_range, ev_type, make):
    yr0, yr1 = yr_range
    gl = df_global[(df_global.Year >= yr0) & (df_global.Year <= yr1)]
    bat = df_battery

    # 1. Global sales stacked area by region
    reg_trend = gl.groupby(['Year','Region'])['Total'].sum().reset_index()
    region_order = ['Asia-Pacific','Europe','Americas','Rest of World']
    clrs = {'Asia-Pacific':GREEN,'Europe':BLUE,'Americas':AMBER,'Rest of World':PURPLE}
    fig1 = go.Figure()
    for reg in region_order:
        s = reg_trend[reg_trend.Region==reg]
        if s.empty: continue
        fig1.add_trace(go.Scatter(
            x=s.Year, y=s.Total, name=reg, stackgroup='one', mode='lines',
            fill='tonexty', line=dict(color=clrs.get(reg,MUTED), width=1.5),
            hovertemplate=f'<b>{reg}</b> %{{x}}: %{{y:.2f}}M<extra></extra>',
        ))
    fig1.update_layout(**_layout(height=310))
    fig1.update_layout(yaxis_title='Sales (M units)', hovermode='x unified')

    # 2. Battery cost
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=bat.Year, y=bat.Cost_kWh, mode='lines+markers',
        line=dict(color=PURPLE, width=3), marker=dict(size=7, color=PURPLE),
        fill='tozeroy', fillcolor=f'{PURPLE}18',
        hovertemplate='%{x}: <b>$%{y}</b>/kWh<extra></extra>',
    ))
    fig2.add_hline(y=100, line=dict(color=GREEN, dash='dash', width=1.5),
                   annotation_text='$100 target', annotation_font_color=GREEN,
                   annotation_position='bottom right')
    fig2.update_layout(**_layout(height=310), showlegend=False)
    fig2.update_layout(yaxis_title='Battery Cost ($/kWh)')

    # 3. Top countries bar
    ctry = gl.groupby('Country')['Total'].sum().sort_values(ascending=False).head(10).reset_index()
    ctry = ctry.sort_values('Total')
    fig3 = go.Figure(go.Bar(
        x=ctry.Total, y=ctry.Country, orientation='h',
        marker=dict(color=PALETTE[:len(ctry)], opacity=0.85),
        hovertemplate='<b>%{y}</b>: %{x:.2f}M<extra></extra>',
    ))
    fig3.update_layout(**_layout(height=310), showlegend=False)
    fig3.update_layout(xaxis_title='Total Sales (M units)', margin=dict(l=120,r=10,t=20,b=30))

    # 4. WA vs global: WA fleet size vs US global sales (indexed to 2015)
    d_wa = _filter(yr_range, ev_type, make)
    wa_yr = d_wa.groupby('Year').size().reset_index(name='WA_Count')
    us_gl = gl[gl.Country=='USA'][['Year','Total']].rename(columns={'Total':'US_Sales_M'})
    merged = wa_yr.merge(us_gl, on='Year', how='inner')
    merged['WA_Share_pct'] = merged.WA_Count / (merged.US_Sales_M * 1e6) * 100

    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        x=merged.Year, y=merged.WA_Share_pct, name='WA % of US EV Sales',
        marker=dict(color=GREEN, opacity=0.8),
        hovertemplate='%{x}: WA = <b>%{y:.1f}%</b> of US<extra></extra>',
    ))
    fig4.update_layout(**_layout(height=310))
    fig4.update_layout(yaxis_title='WA Share of US EV Market (%)')

    return fig1, fig2, fig3, fig4


# ══════════════════════════════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    app.run(debug=True, port=8050)
