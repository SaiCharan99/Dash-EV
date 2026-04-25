import os
import dash
from dash import dcc, html, Input, Output

from core.design_tokens import (
    BG, PANEL, TEXT, MUTED, SUBTLE, SEP,
    BLUE, GREEN, ORANGE, PURPLE, TEAL,
    NAV_BG, NAV_TEXT, NAV_MUTE,
)
from core.layout_helpers import _panel, _ph, _row, _pill_label

from products.energy_dashboard.data import NEM_REGIONS, SEASONS

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
server = app.server


def _kpi_tile_style(accent):
    return {
        'background': PANEL,
        'borderRadius': '16px',
        'boxShadow': '0 2px 12px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04)',
        'padding': '22px 24px', 'flex': '1', 'minWidth': '150px',
        'borderTop': f'3px solid {accent}',
    }


_YEAR_MARKS = {
    y: {'label': str(y), 'style': {'color': SUBTLE, 'fontSize': '10px'}}
    for y in range(2015, 2025) if y % 2 == 1
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
    s.update({'color': NAV_TEXT, 'fontWeight': '600', 'borderBottom': f'2px solid {GREEN}'})
    return s


app.layout = html.Div([

    html.Div([
        html.Div([
            html.Span('AU', style={'fontWeight': '800', 'color': NAV_TEXT, 'fontSize': '14px',
                                   'letterSpacing': '-0.3px'}),
            html.Span('  Energy Transition', style={'fontWeight': '400', 'color': NAV_MUTE,
                                                    'fontSize': '14px'}),
        ], style={'whiteSpace': 'nowrap'}),

        html.Div([
            dcc.Tabs(id='en-main-tabs', value='demand', children=[
                dcc.Tab(label='Demand',           value='demand',     style=_ts(), selected_style=_tss()),
                dcc.Tab(label='Generation Mix',   value='generation', style=_ts(), selected_style=_tss()),
                dcc.Tab(label='Economics & LCOE', value='economics',  style=_ts(), selected_style=_tss()),
                dcc.Tab(label='Renewables',       value='renewables', style=_ts(), selected_style=_tss()),
                dcc.Tab(label='State Comparison', value='comparison', style=_ts(), selected_style=_tss()),
            ], colors={'border': 'transparent', 'primary': GREEN, 'background': 'transparent'},
               style={'border': 'none'}),
        ], style={'flex': '1', 'display': 'flex', 'justifyContent': 'center'}),

        html.A('← Home', href='/', style={
            'fontSize': '12px', 'color': NAV_MUTE, 'textDecoration': 'none',
            'whiteSpace': 'nowrap',
        }),
    ], style={
        'background': NAV_BG, 'padding': '0 32px',
        'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between',
        'position': 'sticky', 'top': '0', 'zIndex': '100', 'minHeight': '52px',
    }),

    html.Div([

        html.Div([
            html.H1('Australian Energy Transition', style={
                'fontSize': '28px', 'fontWeight': '700', 'color': TEXT,
                'letterSpacing': '-0.6px', 'margin': '0',
            }),
            html.P('NEM Regions · 2015–2024 · Real AEMO Data via OpenElectricity',
                   style={'fontSize': '13px', 'color': MUTED, 'marginTop': '5px'}),
        ], style={'padding': '32px 32px 0'}),

        html.Div([
            html.Div([
                _pill_label('Year Range'),
                dcc.RangeSlider(
                    id='en-yr-slider', min=2015, max=2024, step=1, value=[2015, 2024],
                    marks=_YEAR_MARKS, allowCross=False,
                    tooltip={'placement': 'bottom', 'always_visible': False},
                ),
            ], style={'flex': '3', 'minWidth': '220px'}),
            html.Div(style={'width': '1px', 'background': SEP, 'alignSelf': 'stretch'}),
            html.Div([
                _pill_label('Regions'),
                dcc.Dropdown(
                    id='en-region-filter',
                    options=[{'label': r, 'value': r} for r in NEM_REGIONS],
                    value=NEM_REGIONS, multi=True, clearable=False,
                    style={'minWidth': '220px'},
                ),
            ], style={'flex': '2'}),
            html.Div(style={'width': '1px', 'background': SEP, 'alignSelf': 'stretch'}),
            html.Div([
                _pill_label('Season'),
                dcc.RadioItems(
                    id='en-season-filter', value='All', inline=True,
                    options=[{'label': f'  {s.capitalize()}', 'value': s.capitalize()}
                             for s in ['All'] + SEASONS],
                    inputStyle={'marginRight': '4px'},
                    labelStyle={'marginRight': '14px', 'color': TEXT,
                                'fontSize': '13px', 'cursor': 'pointer'},
                ),
            ], style={'flex': '2'}),
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
            html.Div(id='en-kpi-total',    style=_kpi_tile_style(GREEN)),
            html.Div(id='en-kpi-peak',     style=_kpi_tile_style(BLUE)),
            html.Div(id='en-kpi-renew',    style=_kpi_tile_style(TEAL)),
            html.Div(id='en-kpi-price',    style=_kpi_tile_style(ORANGE)),
            html.Div(id='en-kpi-yoy',      style=_kpi_tile_style(PURPLE)),
        ], style={'display': 'flex', 'gap': '16px', 'padding': '20px 32px 0',
                  'flexWrap': 'wrap'}),

        html.Div(id='en-tab-content'),

    ], style={'background': BG, 'minHeight': 'calc(100vh - 52px)'}),

    html.Div(
        'AEMO · OpenElectricity · CSIRO GenCost 2024-25 · Dash & Plotly',
        style={
            'textAlign': 'center', 'padding': '18px', 'color': SUBTLE,
            'fontSize': '11px', 'background': PANEL, 'borderTop': f'1px solid {SEP}',
        }),

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
    P = '20px 32px 32px'
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
