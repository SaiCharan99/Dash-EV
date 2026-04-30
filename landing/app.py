import os
import dash
from dash import html

from core.design_tokens import (
    BG, PANEL, TEXT, MUTED, SUBTLE, SEP,
    BLUE, GREEN, NAV_BG, NAV_TEXT, NAV_MUTE,
    CARD_BORDER, CARD_SHADOW,
)

app = dash.Dash(
    __name__,
    requests_pathname_prefix='/',
    assets_folder=os.path.join(os.path.dirname(__file__), '..', 'assets'),
    title='Energy Platform',
)
server = app.server


def _pill(text, color):
    return html.Span(text, style={
        'fontSize': '11px', 'fontWeight': '600',
        'color': color,
        'background': f'{color}15',
        'padding': '4px 11px',
        'borderRadius': '20px',
        'letterSpacing': '0.2px',
        'border': f'1px solid {color}25',
    })


def _stat(value, label):
    return html.Div([
        html.Div(value, style={
            'fontSize': '22px', 'fontWeight': '700', 'color': TEXT,
            'letterSpacing': '-0.5px', 'lineHeight': '1',
            'fontVariantNumeric': 'tabular-nums',
        }),
        html.Div(label, style={
            'fontSize': '11px', 'color': SUBTLE, 'marginTop': '4px',
            'fontWeight': '500', 'letterSpacing': '0.2px',
        }),
    ], style={'textAlign': 'center'})


def _product_card(title, subtitle, description, href, accent, tags, stats):
    return html.A(href=href, style={'textDecoration': 'none', 'flex': '1',
                                    'minWidth': '300px', 'maxWidth': '500px'}, children=[
        html.Div([
            # accent stripe
            html.Div(style={'height': '3px', 'background': accent}),

            html.Div([
                # header
                html.Div([
                    html.Div(title, style={
                        'fontSize': '21px', 'fontWeight': '700', 'color': TEXT,
                        'letterSpacing': '-0.4px', 'lineHeight': '1.2',
                    }),
                    html.Div(subtitle, style={
                        'fontSize': '12px', 'color': SUBTLE, 'marginTop': '5px',
                        'fontWeight': '500',
                    }),
                ]),

                # description
                html.P(description, style={
                    'fontSize': '14px', 'color': MUTED, 'marginTop': '16px',
                    'lineHeight': '1.65', 'marginBottom': '0',
                }),

                # stats row
                html.Div(stats, style={
                    'display': 'flex', 'gap': '28px', 'marginTop': '24px',
                    'paddingTop': '20px', 'borderTop': f'1px solid {SEP}',
                    'flexWrap': 'wrap',
                }),

                # tags + CTA
                html.Div([
                    html.Div([_pill(t, accent) for t in tags],
                             style={'display': 'flex', 'gap': '7px', 'flexWrap': 'wrap', 'flex': '1'}),
                    html.Div([
                        html.Span('Open  ', style={'fontWeight': '600', 'fontSize': '13px', 'color': accent}),
                        html.Span('→', style={'color': accent, 'fontSize': '15px'}),
                    ], style={'display': 'flex', 'alignItems': 'center', 'whiteSpace': 'nowrap'}),
                ], style={'display': 'flex', 'alignItems': 'center',
                          'justifyContent': 'space-between', 'marginTop': '20px'}),

            ], style={'padding': '26px 28px 28px'}),
        ], style={
            'background': PANEL,
            'borderRadius': '20px',
            'border': f'1px solid {CARD_BORDER}',
            'boxShadow': CARD_SHADOW,
            'overflow': 'hidden',
        }, className='landing-card'),
    ])


app.layout = html.Div([

    # ── nav ──────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Span('Energy', style={
                'fontWeight': '700', 'color': NAV_TEXT, 'fontSize': '14px',
                'letterSpacing': '-0.3px',
            }),
            html.Span('  Platform', style={
                'fontWeight': '400', 'color': NAV_MUTE, 'fontSize': '14px',
            }),
        ]),
        html.Div('data.wa.gov · AEMO · CSIRO GenCost', style={
            'fontSize': '11.5px', 'color': NAV_MUTE, 'letterSpacing': '0.1px',
        }),
    ], style={
        'background': 'rgba(28,28,30,0.88)',
        'backdropFilter': 'blur(20px) saturate(180%)',
        'WebkitBackdropFilter': 'blur(20px) saturate(180%)',
        'padding': '0 40px',
        'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between',
        'minHeight': '56px',
        'position': 'sticky', 'top': '0', 'zIndex': '100',
        'borderBottom': '1px solid rgba(255,255,255,0.06)',
    }),

    # ── hero ──────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Div('Portfolio', style={
                'fontSize': '12px', 'fontWeight': '600', 'color': BLUE,
                'letterSpacing': '1.2px', 'textTransform': 'uppercase',
                'marginBottom': '20px',
            }),
            html.H1('Energy Intelligence\nPlatform', style={
                'fontSize': 'clamp(36px, 5vw, 58px)',
                'fontWeight': '800',
                'color': TEXT,
                'letterSpacing': '-1.5px',
                'margin': '0',
                'lineHeight': '1.08',
                'whiteSpace': 'pre-line',
            }),
            html.P(
                'Data-driven tools for understanding EV adoption and the clean energy transition.',
                style={
                    'color': MUTED, 'fontSize': '17px', 'marginTop': '20px',
                    'maxWidth': '480px', 'lineHeight': '1.65',
                    'fontWeight': '400',
                }),
        ], style={'textAlign': 'center', 'padding': '80px 40px 56px'}),

        # ── product cards ─────────────────────────────────────────────
        html.Div([
            _product_card(
                title='EV Market Intelligence',
                subtitle='Washington State · 280,000+ registered vehicles',
                description=(
                    'Fleet composition, manufacturer trends, county-level geographic '
                    'distribution, and global EV context from 2015 to 2025.'
                ),
                href='/ev/',
                accent=BLUE,
                tags=['BEV / PHEV', 'County Maps', 'Global Context'],
                stats=[
                    _stat('280K+', 'Vehicles'),
                    _stat('11 yr', 'History'),
                    _stat('39', 'Counties'),
                ],
            ),
            _product_card(
                title='Australian Energy Transition',
                subtitle='NEM Regions · 2015–2024 · AEMO Data',
                description=(
                    'Electricity demand, generation mix evolution, renewable growth '
                    'trajectories, and LCOE economics across NSW, VIC, QLD, SA and TAS.'
                ),
                href='/energy/',
                accent=GREEN,
                tags=['Demand', 'Generation Mix', 'LCOE Economics'],
                stats=[
                    _stat('5', 'NEM Regions'),
                    _stat('10 yr', 'History'),
                    _stat('CSIRO', 'LCOE Source'),
                ],
            ),
        ], style={
            'display': 'flex', 'gap': '24px', 'justifyContent': 'center',
            'padding': '0 40px 88px', 'flexWrap': 'wrap',
        }),

    ], style={
        'background': f'linear-gradient(180deg, {BG} 0%, #FAFAFC 100%)',
        'minHeight': 'calc(100vh - 56px)',
    }),

    # ── footer ────────────────────────────────────────────────────────
    html.Div([
        html.Div(
            'Washington State DOL  ·  AEMO  ·  CSIRO GenCost 2024-25  ·  OpenElectricity  ·  Dash & Plotly',
            style={'color': SUBTLE, 'fontSize': '11px'},
        ),
    ], style={
        'textAlign': 'center', 'padding': '22px 40px',
        'background': PANEL, 'borderTop': f'1px solid {SEP}',
    }),

], style={'fontFamily': 'Inter, -apple-system, sans-serif'})
