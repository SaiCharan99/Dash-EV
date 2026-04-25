import os
import dash
from dash import html

from core.design_tokens import (
    BG, PANEL, TEXT, MUTED, SUBTLE, SEP,
    BLUE, GREEN, NAV_BG, NAV_TEXT, NAV_MUTE,
)

app = dash.Dash(
    __name__,
    requests_pathname_prefix='/',
    assets_folder=os.path.join(os.path.dirname(__file__), '..', 'assets'),
    title='Energy Platform',
)
server = app.server

_PANEL_STYLE = {
    'background': PANEL,
    'borderRadius': '20px',
    'boxShadow': '0 4px 24px rgba(0,0,0,0.07), 0 1px 4px rgba(0,0,0,0.04)',
    'overflow': 'hidden',
    'transition': 'box-shadow 0.2s',
    'flex': '1',
    'minWidth': '300px',
    'maxWidth': '480px',
}


def _pill(text, color):
    return html.Span(text, style={
        'fontSize': '11px', 'fontWeight': '600',
        'color': color,
        'background': f'{color}18',
        'padding': '3px 10px', 'borderRadius': '20px',
        'letterSpacing': '0.3px',
    })


def _product_card(title, subtitle, description, href, accent, tags):
    return html.A(href=href, style={'textDecoration': 'none', 'flex': '1',
                                    'minWidth': '300px', 'maxWidth': '480px'}, children=[
        html.Div([
            html.Div(style={
                'height': '4px', 'background': accent,
            }),
            html.Div([
                html.Div(title, style={
                    'fontSize': '22px', 'fontWeight': '700', 'color': TEXT,
                    'letterSpacing': '-0.4px', 'lineHeight': '1.2',
                }),
                html.Div(subtitle, style={
                    'fontSize': '12px', 'color': SUBTLE, 'marginTop': '6px',
                    'fontWeight': '500',
                }),
                html.P(description, style={
                    'fontSize': '14px', 'color': MUTED, 'marginTop': '16px',
                    'lineHeight': '1.6', 'marginBottom': '20px',
                }),
                html.Div([_pill(t, accent) for t in tags],
                         style={'display': 'flex', 'gap': '8px', 'flexWrap': 'wrap',
                                'marginBottom': '24px'}),
                html.Div([
                    html.Span('Open', style={'fontWeight': '600', 'fontSize': '14px',
                                             'color': accent}),
                    html.Span('  →', style={'color': accent, 'fontSize': '16px'}),
                ], style={'display': 'flex', 'alignItems': 'center'}),
            ], style={'padding': '28px 28px 32px'}),
        ], style=_PANEL_STYLE),
    ])


app.layout = html.Div([

    html.Div([
        html.Div([
            html.Span('Energy', style={
                'fontWeight': '800', 'color': NAV_TEXT, 'fontSize': '15px',
                'letterSpacing': '-0.3px',
            }),
            html.Span('  Platform', style={
                'fontWeight': '400', 'color': NAV_MUTE, 'fontSize': '15px',
            }),
        ]),
        html.Div('data.wa.gov · AEMO · CSIRO GenCost', style={
            'fontSize': '11px', 'color': NAV_MUTE,
        }),
    ], style={
        'background': NAV_BG, 'padding': '0 40px',
        'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between',
        'minHeight': '52px',
    }),

    html.Div([

        html.Div([
            html.H1('Energy Intelligence Platform', style={
                'fontSize': '42px', 'fontWeight': '700', 'color': TEXT,
                'letterSpacing': '-1px', 'margin': '0', 'lineHeight': '1.1',
            }),
            html.P(
                'Data-driven tools for understanding EV adoption and the clean energy transition.',
                style={
                    'color': MUTED, 'fontSize': '16px', 'marginTop': '16px',
                    'maxWidth': '520px', 'lineHeight': '1.6',
                }),
        ], style={'textAlign': 'center', 'padding': '72px 40px 48px'}),

        html.Div([
            _product_card(
                title='EV Market Intelligence',
                subtitle='Washington State · 280,000+ registered vehicles',
                description=(
                    'Fleet composition, manufacturer trends, geographic distribution '
                    'across WA counties, and global EV context from 2015 to 2025.'
                ),
                href='/ev/',
                accent=BLUE,
                tags=['BEV / PHEV', 'County Maps', 'Global Context'],
            ),
            _product_card(
                title='Australian Energy Transition',
                subtitle='NEM Regions · 2015–2024 · Real AEMO Data',
                description=(
                    'Electricity demand patterns, generation mix evolution, renewable '
                    'growth trajectories, and LCOE economics across NSW, VIC, QLD, SA, and TAS.'
                ),
                href='/energy/',
                accent=GREEN,
                tags=['Demand & Seasons', 'Generation Mix', 'LCOE Economics'],
            ),
        ], style={
            'display': 'flex', 'gap': '24px', 'justifyContent': 'center',
            'padding': '0 40px 80px', 'flexWrap': 'wrap',
        }),

    ], style={'background': BG, 'minHeight': 'calc(100vh - 52px)'}),

    html.Div(
        'Washington State DOL  ·  AEMO  ·  CSIRO GenCost 2024-25  ·  OpenElectricity  ·  Built with Dash & Plotly',
        style={
            'textAlign': 'center', 'padding': '20px', 'color': SUBTLE,
            'fontSize': '11px', 'background': PANEL, 'borderTop': f'1px solid {SEP}',
        }),

], style={'fontFamily': 'Inter, -apple-system, sans-serif'})
