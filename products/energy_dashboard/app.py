import os
import dash
from dash import dcc, html, Input, Output

from core.design_tokens import (
    BG, PANEL, TEXT, SECONDARY, MUTED, SUBTLE, SEP,
    BLUE, GREEN, ORANGE, RED, PURPLE, TEAL,
    CARD_BORDER, CARD_SHADOW,
)
from core.layout_helpers import _panel, _ph, _row, _pill_label
from core.chart_factory import _rgba
from core.dash_utils import ACCESSIBLE_INDEX

from products.energy_dashboard.data import NEM_REGIONS, SEASONS
from core.app_cache import flask_cache

import products.energy_dashboard.callbacks.cb_kpis        as _kpis
import products.energy_dashboard.callbacks.cb_demand       as _demand
import products.energy_dashboard.callbacks.cb_generation   as _generation
import products.energy_dashboard.callbacks.cb_economics    as _economics
import products.energy_dashboard.callbacks.cb_renewables   as _renewables
import products.energy_dashboard.callbacks.cb_comparison   as _comparison

app = dash.Dash(
    __name__,
    requests_pathname_prefix='/energy/',
    assets_folder=os.path.join(os.path.dirname(__file__), '..', '..', 'assets'),
    suppress_callback_exceptions=True,
    title='AU Energy Transition',
)
app.index_string = ACCESSIBLE_INDEX
server = app.server

flask_cache.init_app(server, config={
    'CACHE_TYPE':            'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300,   # 5 minutes — matches typical user session
})


def _kpi_tile_style(accent):
    return {
        'background': PANEL,
        'borderRadius': '18px',
        'border': f'1px solid {CARD_BORDER}',
        'boxShadow': CARD_SHADOW,
        'padding': '22px 24px', 'flex': '1', 'minWidth': '150px',
    }


_YEAR_MARKS = {
    y: {'label': str(y), 'style': {'color': SUBTLE, 'fontSize': '10px'}}
    for y in range(2015, 2025) if y % 2 == 1
}


# ── about modal helpers ───────────────────────────────────────────────────────
_SL = {'fontSize': '11px', 'fontWeight': '700', 'color': SECONDARY,
       'textTransform': 'uppercase', 'letterSpacing': '0.9px'}

def _about_src(name, desc):
    return html.Div([
        html.Div(name, style={'fontSize': '14px', 'fontWeight': '600', 'color': TEXT, 'lineHeight': '1.3'}),
        html.Div(desc, style={'fontSize': '13px', 'color': SECONDARY, 'marginTop': '3px', 'lineHeight': '1.5'}),
    ], style={
        'borderLeft': f'2px solid {GREEN}',
        'paddingLeft': '14px', 'paddingTop': '2px', 'paddingBottom': '2px',
    })

def _about_step(num, text):
    return html.Div([
        html.Span(f'0{num}', style={
            'fontSize': '11px', 'fontWeight': '700', 'color': GREEN,
            'flexShrink': '0', 'minWidth': '24px', 'letterSpacing': '0.4px',
        }),
        html.Div(text, style={'fontSize': '14px', 'color': TEXT, 'lineHeight': '1.55'}),
    ], style={'display': 'flex', 'gap': '10px', 'alignItems': 'flex-start'})

def _about_pill(name):
    return html.Span(name, style={
        'background': 'rgba(0,0,0,0.04)', 'color': TEXT,
        'border': f'1px solid {SEP}',
        'padding': '4px 10px', 'borderRadius': '6px',
        'fontSize': '12px', 'fontWeight': '500',
    })

_en_about_modal = html.Div(
    id='en-about-modal',
    style={'display': 'none'},
    children=[
        html.Div(id='en-about-backdrop', n_clicks=0, style={
            'position': 'absolute', 'top': '0', 'left': '0', 'right': '0', 'bottom': '0',
            'zIndex': '0',
        }),
        html.Div([
            html.Div(style={'height': '3px', 'background': GREEN}),
            html.Div([
                html.Button('✕', id='en-about-close', style={
                    'position': 'absolute', 'top': '16px', 'right': '16px',
                    'background': 'rgba(0,0,0,0.05)', 'border': 'none', 'borderRadius': '50%',
                    'width': '28px', 'height': '28px', 'fontSize': '12px', 'color': MUTED,
                    'cursor': 'pointer', 'fontFamily': 'Inter, sans-serif',
                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                }),
                html.Div([
                    html.Div('AU', style={
                        'background': GREEN, 'color': '#fff', 'borderRadius': '7px',
                        'padding': '3px 8px', 'fontSize': '11px', 'fontWeight': '700',
                        'letterSpacing': '0.5px', 'display': 'inline-block', 'marginBottom': '14px',
                    }),
                    html.H2('AU Energy Transition', style={
                        'fontSize': '22px', 'fontWeight': '800', 'color': TEXT,
                        'letterSpacing': '-0.5px', 'margin': '0 0 5px',
                    }),
                    html.Div('NEM Regions · 2015-2024', style={'fontSize': '13px', 'color': MUTED}),
                ], style={'marginBottom': '28px'}),
                html.Div('About', style=_SL),
                html.Div(style={'height': '8px'}),
                html.P(
                    "Tracks Australia's electricity sector transition across the National Electricity Market. "
                    "Covers generation by fuel type, demand trends, spot pricing, and LCOE economics "
                    "for all five NEM regions from 2015 to 2024, using real AEMO data.",
                    style={'fontSize': '14px', 'color': TEXT, 'lineHeight': '1.7', 'margin': '0 0 24px'},
                ),
                html.Div('Data Sources', style=_SL),
                html.Div(style={'height': '10px'}),
                html.Div([
                    _about_src('AEMO via OpenElectricity', 'Demand, generation by fuel type, and spot prices for NSW, VIC, QLD, SA, TAS'),
                    _about_src('CSIRO GenCost 2024-25', 'LCOE ranges ($/MWh) and 2030 forward cost projections'),
                    _about_src('Facility Registry', 'Operating capacity snapshot by region and fuel technology'),
                ], style={'display': 'flex', 'flexDirection': 'column', 'gap': '14px', 'marginBottom': '24px'}),
                html.Div('How to Use', style=_SL),
                html.Div(style={'height': '10px'}),
                html.Div([
                    _about_step('1', 'Switch tabs: Demand, Generation Mix, Economics & LCOE, Renewables, State Comparison'),
                    _about_step('2', 'Filter by year range (2015-2024), NEM region, and season'),
                    _about_step('3', 'The KPI strip at the top always reflects the current filter selection'),
                ], style={'display': 'flex', 'flexDirection': 'column', 'gap': '10px', 'marginBottom': '24px'}),
                html.Div('Built With', style=_SL),
                html.Div(style={'height': '10px'}),
                html.Div([
                    _about_pill('Python'),
                    _about_pill('Dash'),
                    _about_pill('Plotly'),
                    _about_pill('Pandas'),
                    _about_pill('FastAPI'),
                    _about_pill('PyArrow'),
                    _about_pill('OpenElectricity'),
                ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '7px'}),
            ], style={'padding': '26px', 'position': 'relative',
                      'maxHeight': 'calc(90vh - 3px)', 'overflowY': 'auto'}),
        ], style={
            'background': PANEL, 'borderRadius': '20px',
            'maxWidth': '520px', 'width': '100%', 'overflow': 'hidden',
            'boxShadow': '0 32px 80px rgba(0,0,0,0.18), 0 0 0 1px rgba(0,0,0,0.07)',
            'position': 'relative', 'zIndex': '1',
        }),
    ],
)


app.layout = html.Div([
    html.A('Skip to main content', href='#main-content', className='skip-link'),

    # ── nav ───────────────────────────────────────────────────────────
    html.Nav([
        html.Div([
            html.Span('AU', style={
                'fontWeight': '700', 'color': TEXT, 'fontSize': '14px',
                'letterSpacing': '-0.3px',
            }),
            html.Span('  Energy Transition', style={
                'fontWeight': '400', 'color': MUTED, 'fontSize': '14px',
            }),
        ], style={'whiteSpace': 'nowrap'}),

        html.Div([
            dcc.RadioItems(
                id='en-main-tabs', value='demand',
                options=[
                    {'label': 'Demand',           'value': 'demand'},
                    {'label': 'Generation Mix',   'value': 'generation'},
                    {'label': 'Economics & LCOE', 'value': 'economics'},
                    {'label': 'Renewables',       'value': 'renewables'},
                    {'label': 'State Comparison', 'value': 'comparison'},
                ],
                inline=True, className='nav-tabs',
                inputStyle={}, labelStyle={},
            ),
        ], style={'flex': '1', 'display': 'flex', 'justifyContent': 'center'}),

        html.Div([
            html.Button('About', id='en-about-btn', style={
                'background': 'none', 'border': f'1px solid {CARD_BORDER}',
                'borderRadius': '8px', 'padding': '5px 12px',
                'fontSize': '12px', 'color': MUTED, 'fontFamily': 'Inter, sans-serif',
                'fontWeight': '500', 'letterSpacing': '0.1px', 'whiteSpace': 'nowrap',
            }),
            html.A('← Home', href='/', style={
                'fontSize': '12px', 'color': MUTED, 'textDecoration': 'none',
                'whiteSpace': 'nowrap', 'letterSpacing': '0.1px',
            }, **{"aria-label": "Back to home"}),
        ], style={'display': 'flex', 'alignItems': 'center', 'gap': '12px'}),
    ], **{"aria-label": "Energy dashboard navigation"}, className='glass-nav', style={
        'padding': '0 32px',
        'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between',
        'position': 'sticky', 'top': '0', 'zIndex': '100', 'minHeight': '56px',
    }),

    html.Main([

        # ── page header ───────────────────────────────────────────────
        html.Div([
            html.H1('Australian Energy Transition', style={
                'fontSize': '32px', 'fontWeight': '800', 'color': TEXT,
                'letterSpacing': '-0.8px', 'margin': '0', 'lineHeight': '1.1',
            }),
            html.P('NEM Regions · 2015–2024 · AEMO Data via OpenElectricity',
                   style={'fontSize': '13px', 'color': MUTED, 'marginTop': '7px',
                          'fontWeight': '400'}),
        ], style={'padding': '36px 36px 0'}),

        # ── filter bar ────────────────────────────────────────────────
        html.Div([
            html.Div([
                _pill_label('Year Range', 'lbl-en-yr'),
                dcc.RangeSlider(
                    id='en-yr-slider', min=2015, max=2024, step=1, value=[2015, 2024],
                    marks=_YEAR_MARKS, allowCross=False,
                    tooltip={'placement': 'bottom', 'always_visible': False},
                ),
            ], style={'flex': '3', 'minWidth': '240px'}),

            html.Div(style={'width': '1px', 'background': SEP, 'alignSelf': 'stretch'},
                     **{"aria-hidden": "true"}),

            html.Div([
                _pill_label('Regions', 'lbl-en-regions'),
                dcc.Dropdown(
                    id='en-region-filter',
                    options=[{'label': r, 'value': r} for r in NEM_REGIONS],
                    value=NEM_REGIONS, multi=True, clearable=False,
                    style={'minWidth': '220px'},
                ),
            ], style={'flex': '2'}),

            html.Div(style={'width': '1px', 'background': SEP, 'alignSelf': 'stretch'},
                     **{"aria-hidden": "true"}),

            html.Div([
                _pill_label('Season', 'lbl-en-season'),
                dcc.RadioItems(
                    id='en-season-filter', value='All', inline=True,
                    options=[{'label': s.capitalize(), 'value': s.capitalize()}
                             for s in ['All'] + SEASONS],
                    className='seg-control',
                    inputStyle={}, labelStyle={},
                ),
            ], style={'flex': '2'}),
        ], role='group', **{"aria-label": "Dashboard filters"}, style={
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
            html.Div(id='en-kpi-total', style=_kpi_tile_style(GREEN),
                     className='dash-card', **{"aria-live": "polite", "aria-atomic": "true"}),
            html.Div(id='en-kpi-peak',  style=_kpi_tile_style(BLUE),
                     className='dash-card', **{"aria-live": "polite", "aria-atomic": "true"}),
            html.Div(id='en-kpi-renew', style=_kpi_tile_style(TEAL),
                     className='dash-card', **{"aria-live": "polite", "aria-atomic": "true"}),
            html.Div(id='en-kpi-price', style=_kpi_tile_style(ORANGE),
                     className='dash-card', **{"aria-live": "polite", "aria-atomic": "true"}),
            html.Div(id='en-kpi-yoy',   style=_kpi_tile_style(PURPLE),
                     className='dash-card', **{"aria-live": "polite", "aria-atomic": "true"}),
        ], style={'display': 'flex', 'gap': '16px', 'padding': '20px 36px 0', 'flexWrap': 'wrap'}),

        html.Div(id='en-tab-content'),

    ], id='main-content', style={'background': BG, 'minHeight': 'calc(100vh - 56px)'}),

    # ── footer ────────────────────────────────────────────────────────
    html.Footer([
        html.Div(
            'AEMO · OpenElectricity · CSIRO GenCost 2024-25 · Dash & Plotly',
            style={'color': SUBTLE, 'fontSize': '11px'},
        ),
    ], style={
        'textAlign': 'center', 'padding': '20px',
        'background': PANEL, 'borderTop': f'1px solid {SEP}',
    }),

    _en_about_modal,

], style={'fontFamily': 'Inter, -apple-system, sans-serif'})


# Register all callbacks
_kpis.register(app)
_demand.register(app)
_generation.register(app)
_economics.register(app)
_renewables.register(app)
_comparison.register(app)


# Tab router
@app.callback(Output('en-tab-content', 'children'), Input('en-main-tabs', 'value'))
def render_tab(tab):
    P = '24px 36px 36px'
    cfg = {'displayModeBar': False}

    if tab == 'demand':
        return html.Div([
            _row(
                _panel([
                    _ph('Electricity Demand by Region', 'Monthly GWh · 2015–2024'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='dem-timeseries', config=cfg),
                ], flex=2),
                _panel([
                    _ph('Seasonal Distribution', 'GWh by season · box plot'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='dem-seasonal-box', config=cfg),
                ]),
            ),
            _row(
                _panel([
                    _ph('Demand Heatmap', 'Avg daily GW · month × year'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='dem-heatmap', config=cfg),
                ]),
            ),
        ], style={'padding': P})

    if tab == 'generation':
        return html.Div([
            _row(
                _panel([
                    _ph('Generation by Source', 'Annual GWh · 2015–2024'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='gen-trend-lines', config=cfg),
                ], flex=2),
                _panel([
                    _ph('Current Year Mix', 'Share of total generation'),
                    dcc.Graph(id='gen-donut', config=cfg),
                    html.Div(id='gen-donut-legend'),
                ]),
            ),
            _row(
                _panel([
                    _ph('Annual Generation Stack', 'GWh by fuel type'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='gen-stacked-bar', config=cfg),
                ], flex=2),
                _panel([
                    _ph('Monthly Generation', 'Last 3 years · stacked area'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='gen-monthly-area', config=cfg),
                ]),
            ),
        ], style={'padding': P})

    if tab == 'economics':
        return html.Div([
            _row(
                _panel([
                    _ph('LCOE by Technology', '$/MWh · CSIRO GenCost 2024-25'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='econ-lcoe-range', config=cfg),
                ]),
                _panel([
                    _ph('Cost Trajectories 2015–2030', '$/MWh · actuals + projections'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='econ-lcoe-trend', config=cfg),
                ]),
            ),
            _row(
                _panel([
                    _ph('Spot Price vs LCOE', '$/MWh · renewables crossover'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='econ-price-vs-lcoe', config=cfg),
                ], flex=2),
                _panel([
                    _ph('Demand vs Average Cost', 'TWh (bars) · $/MWh (line)'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='econ-demand-cost', config=cfg),
                ]),
            ),
        ], style={'padding': P})

    if tab == 'renewables':
        return html.Div([
            _row(
                _panel([
                    _ph('Renewable Share by State', '% of total generation · by year'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='ren-share-bar', config=cfg),
                ], flex=2),
                _panel([
                    _ph('Capacity Factor Heatmap', 'Month × Region · solar & wind'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='ren-cf-heatmap', config=cfg),
                ]),
            ),
            _row(
                _panel([
                    _ph('Net GWh Change Since 2015', 'By source · waterfall'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='ren-growth-waterfall', config=cfg),
                ]),
            ),
        ], style={'padding': P})

    if tab == 'comparison':
        return html.Div([
            _row(
                _panel([
                    _ph('Generation by State', 'GWh by source · selected year'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='sc-grouped-bar', config=cfg),
                ], flex=2),
                _panel([
                    _ph('State Radar', 'Renewable% · Price · Peak · Capacity Factor'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='sc-radar', config=cfg),
                ]),
            ),
            _row(
                _panel([
                    _ph('Australia Map', 'Bubble = demand · colour = avg spot price'),
                    html.Div(style={'height': '12px'}),
                    dcc.Graph(id='sc-price-map', config=cfg),
                ]),
            ),
        ], style={'padding': P})


app.clientside_callback(
    """
    function(open_n, close_n, backdrop_n) {
        var ctx = dash_clientside.callback_context;
        if (!ctx.triggered || !ctx.triggered.length) return window.dash_clientside.no_update;
        var pid = ctx.triggered[0].prop_id;
        if (pid.indexOf('en-about-btn') !== -1) {
            return {display:'flex', position:'fixed', top:'0', right:'0', bottom:'0', left:'0',
                    zIndex:'1000', alignItems:'center', justifyContent:'center',
                    background:'rgba(248,248,252,0.62)',
                    backdropFilter:'blur(28px) saturate(160%)',
                    WebkitBackdropFilter:'blur(28px) saturate(160%)',
                    padding:'24px', overflowY:'auto'};
        }
        return {display: 'none'};
    }
    """,
    Output('en-about-modal', 'style'),
    [Input('en-about-btn', 'n_clicks'), Input('en-about-close', 'n_clicks'),
     Input('en-about-backdrop', 'n_clicks')],
    prevent_initial_call=True,
)
