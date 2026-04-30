import os
import dash
from dash import html

from core.design_tokens import (
    BG, PANEL, TEXT, MUTED, SUBTLE, SEP,
    BLUE, GREEN, NAV_BG, NAV_TEXT, NAV_MUTE,
    CARD_BORDER, CARD_SHADOW,
)
from core.dash_utils import ACCESSIBLE_INDEX

app = dash.Dash(
    __name__,
    requests_pathname_prefix='/',
    assets_folder=os.path.join(os.path.dirname(__file__), '..', 'assets'),
    title='Energy Platform',
)
app.index_string = ACCESSIBLE_INDEX
server = app.server

# ── Switch between layouts ─────────────────────────────────────────
# Set LAYOUT = 'A' for Minimal Centered  (clean, symmetric, Apple-style)
# Set LAYOUT = 'B' for Bold Hero + Cards (dark hero banner, high contrast)
LAYOUT = 'A'


# ── Shared components ──────────────────────────────────────────────
def _nav():
    return html.Nav([
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
            'fontSize': '11.5px', 'color': NAV_MUTE,
        }),
    ], aria_label='Site navigation', style={
        'background': 'rgba(28,28,30,0.90)',
        'backdropFilter': 'blur(20px) saturate(180%)',
        'WebkitBackdropFilter': 'blur(20px) saturate(180%)',
        'padding': '0 48px',
        'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between',
        'minHeight': '56px',
        'position': 'sticky', 'top': '0', 'zIndex': '100',
        'borderBottom': '1px solid rgba(255,255,255,0.07)',
    })


def _footer():
    return html.Footer(
        'Washington State DOL  ·  AEMO  ·  CSIRO GenCost 2024-25  ·  OpenElectricity  ·  Dash & Plotly',
        style={
            'textAlign': 'center', 'padding': '22px 48px',
            'color': SUBTLE, 'fontSize': '11px',
            'background': PANEL, 'borderTop': f'1px solid {SEP}',
        })


def _pill(text, color):
    return html.Span(text, style={
        'fontSize': '11px', 'fontWeight': '600',
        'color': color,
        'background': f'{color}14',
        'padding': '4px 12px',
        'borderRadius': '20px',
        'border': f'1px solid {color}22',
        'letterSpacing': '0.1px',
    })


# ══════════════════════════════════════════════════════════════════
# OPTION A  —  Minimal Centered  (symmetric, spacious, Apple.com)
# ══════════════════════════════════════════════════════════════════
def _card_a(title, subtitle, description, href, accent, tags):
    return html.A(href=href, aria_label=f'Open {title} dashboard', style={'textDecoration': 'none', 'flex': '1',
                                    'minWidth': '320px', 'maxWidth': '480px'}, children=[
        html.Div([
            html.Div(style={'height': '3px', 'background': accent, 'borderRadius': '0'}),
            html.Div([

                html.Div([
                    html.Div(title, style={
                        'fontSize': '20px', 'fontWeight': '700', 'color': TEXT,
                        'letterSpacing': '-0.4px', 'lineHeight': '1.25',
                    }),
                    html.Div(subtitle, style={
                        'fontSize': '12px', 'color': SUBTLE,
                        'marginTop': '5px', 'fontWeight': '500',
                    }),
                ]),

                html.P(description, style={
                    'fontSize': '14px', 'color': MUTED, 'marginTop': '16px',
                    'lineHeight': '1.65', 'margin': '16px 0 0 0',
                }),

                html.Div(style={
                    'height': '1px', 'background': SEP, 'margin': '20px 0',
                }),

                html.Div([_pill(t, accent) for t in tags],
                         style={'display': 'flex', 'gap': '7px', 'flexWrap': 'wrap',
                                'marginBottom': '20px'}),

                html.Div([
                    html.Span('Open  ', style={
                        'fontWeight': '600', 'fontSize': '13px', 'color': accent,
                    }),
                    html.Span('→', style={'color': accent, 'fontSize': '15px'}),
                ], style={'display': 'flex', 'alignItems': 'center'}),

            ], style={'padding': '24px 26px 28px'}),
        ], style={
            'background': PANEL,
            'borderRadius': '20px',
            'border': f'1px solid {CARD_BORDER}',
            'boxShadow': CARD_SHADOW,
            'overflow': 'hidden',
            'height': '100%',
        }, className='landing-card'),
    ])


layout_a = html.Div([
    html.A('Skip to main content', href='#main-content', className='skip-link'),
    _nav(),

    html.Main([

        # hero — perfectly centred column
        html.Div([
            html.Div('Portfolio', style={
                'fontSize': '11px', 'fontWeight': '700', 'color': BLUE,
                'letterSpacing': '2px', 'textTransform': 'uppercase',
                'marginBottom': '22px',
            }),
            html.H1('Energy Intelligence\nPlatform', style={
                'fontSize': 'clamp(40px, 5.5vw, 64px)',
                'fontWeight': '800', 'color': TEXT,
                'letterSpacing': '-2px', 'margin': '0',
                'lineHeight': '1.06', 'whiteSpace': 'pre-line',
            }),
            html.P(
                'Data-driven tools for understanding EV adoption\nand the clean energy transition.',
                style={
                    'color': MUTED, 'fontSize': '17px',
                    'margin': '20px auto 0', 'lineHeight': '1.65',
                    'fontWeight': '400', 'maxWidth': '440px',
                    'whiteSpace': 'pre-line',
                }),
        ], style={
            'textAlign': 'center',
            'padding': '88px 48px 60px',
            'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center',
        }),

        # cards — equal width, symmetric
        html.Div([
            _card_a(
                title='EV Market Intelligence',
                subtitle='Washington State · 280,000+ registered vehicles',
                description=(
                    'Fleet composition, manufacturer trends, county-level '
                    'geographic distribution, and global EV context from 2015 to 2025.'
                ),
                href='/ev/', accent=BLUE,
                tags=['BEV / PHEV', 'County Maps', 'Manufacturers', 'Global Context'],
            ),
            _card_a(
                title='Australian Energy Transition',
                subtitle='NEM Regions · 2015–2024 · AEMO Data',
                description=(
                    'Electricity demand, generation mix evolution, renewable growth '
                    'trajectories, and LCOE economics across NSW, VIC, QLD, SA and TAS.'
                ),
                href='/energy/', accent=GREEN,
                tags=['Demand', 'Generation Mix', 'LCOE Economics', 'State Comparison'],
            ),
        ], style={
            'display': 'flex', 'gap': '24px',
            'justifyContent': 'center', 'alignItems': 'stretch',
            'padding': '0 48px 96px',
            'flexWrap': 'wrap',
            'maxWidth': '1060px', 'margin': '0 auto',
        }),

    ], id='main-content', style={'background': BG, 'minHeight': 'calc(100vh - 56px)'}),

    _footer(),
], style={'fontFamily': 'Inter, -apple-system, sans-serif'})


# ══════════════════════════════════════════════════════════════════
# OPTION B  —  Bold Hero + Cards  (dark top section, high contrast)
# ══════════════════════════════════════════════════════════════════
def _card_b(title, subtitle, description, href, accent, tags):
    return html.A(href=href, aria_label=f'Open {title} dashboard', style={'textDecoration': 'none', 'flex': '1',
                                    'minWidth': '320px', 'maxWidth': '520px'}, children=[
        html.Div([
            # icon bar
            html.Div([
                html.Div(style={
                    'width': '36px', 'height': '36px', 'borderRadius': '10px',
                    'background': f'{accent}18',
                    'border': f'1px solid {accent}30',
                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                }),
                html.Div([
                    html.Div(title, style={
                        'fontSize': '18px', 'fontWeight': '700', 'color': TEXT,
                        'letterSpacing': '-0.35px', 'lineHeight': '1.2',
                    }),
                    html.Div(subtitle, style={
                        'fontSize': '11.5px', 'color': SUBTLE,
                        'marginTop': '3px', 'fontWeight': '500',
                    }),
                ]),
            ], style={'display': 'flex', 'alignItems': 'center', 'gap': '14px'}),

            html.P(description, style={
                'fontSize': '14px', 'color': MUTED, 'marginTop': '18px',
                'lineHeight': '1.65', 'marginBottom': '0',
            }),

            html.Div(style={'height': '1px', 'background': SEP, 'margin': '20px 0'}),

            html.Div([
                html.Div([_pill(t, accent) for t in tags],
                         style={'display': 'flex', 'gap': '6px', 'flexWrap': 'wrap', 'flex': '1'}),
                html.Div([
                    html.Span('Open', style={
                        'fontWeight': '600', 'fontSize': '13px', 'color': accent,
                    }),
                    html.Span('  →', style={'color': accent, 'fontSize': '14px'}),
                ], style={'display': 'flex', 'alignItems': 'center', 'whiteSpace': 'nowrap',
                           'marginLeft': '12px'}),
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}),

        ], style={
            'background': PANEL,
            'borderRadius': '20px',
            'border': f'1px solid {CARD_BORDER}',
            'boxShadow': CARD_SHADOW,
            'padding': '28px 28px 26px',
            'height': '100%',
        }, className='landing-card'),
    ])


layout_b = html.Div([
    html.A('Skip to main content', href='#main-content', className='skip-link'),
    _nav(),

    html.Main([
        # ── dark hero banner ──────────────────────────────────────────
        html.Div([
            html.Div([
                html.Div('Two dashboards. One platform.', style={
                    'fontSize': '12px', 'fontWeight': '600', 'color': 'rgba(255,255,255,0.45)',
                    'letterSpacing': '1.5px', 'textTransform': 'uppercase',
                    'marginBottom': '24px',
                }),
                html.H1('Energy Intelligence\nPlatform', style={
                    'fontSize': 'clamp(38px, 5vw, 62px)',
                    'fontWeight': '800', 'color': '#FFFFFF',
                    'letterSpacing': '-2px', 'margin': '0',
                    'lineHeight': '1.06', 'whiteSpace': 'pre-line',
                }),
                html.P(
                    'Data-driven tools for understanding EV adoption and the clean energy transition.',
                    style={
                        'color': 'rgba(255,255,255,0.55)', 'fontSize': '16px',
                        'margin': '20px 0 0', 'lineHeight': '1.65',
                        'maxWidth': '420px',
                    }),
            ], style={
                'padding': '80px 48px 80px',
                'maxWidth': '700px', 'margin': '0 auto',
                'textAlign': 'center',
                'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center',
            }),
        ], style={
            'background': 'linear-gradient(160deg, #1C1C1E 0%, #2C2C2E 60%, #1A1A2E 100%)',
            'borderBottom': '1px solid rgba(255,255,255,0.07)',
        }),

        # ── cards section ─────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Div('Choose a dashboard', style={
                    'fontSize': '13px', 'fontWeight': '600', 'color': SUBTLE,
                    'textAlign': 'center', 'marginBottom': '28px',
                    'letterSpacing': '0.2px',
                }),
                html.Div([
                    _card_b(
                        title='EV Market Intelligence',
                        subtitle='Washington State · 280,000+ registered vehicles',
                        description=(
                            'Fleet composition, manufacturer trends, county-level geographic '
                            'distribution, and global EV context from 2015 to 2025.'
                        ),
                        href='/ev/', accent=BLUE,
                        tags=['BEV / PHEV', 'County Maps', 'Global Context'],
                    ),
                    _card_b(
                        title='Australian Energy Transition',
                        subtitle='NEM Regions · 2015–2024 · AEMO Data',
                        description=(
                            'Electricity demand, generation mix evolution, renewable growth '
                            'trajectories and LCOE economics across NSW, VIC, QLD, SA and TAS.'
                        ),
                        href='/energy/', accent=GREEN,
                        tags=['Demand', 'Generation Mix', 'LCOE Economics'],
                    ),
                ], style={
                    'display': 'flex', 'gap': '20px',
                    'justifyContent': 'center', 'alignItems': 'stretch',
                    'flexWrap': 'wrap',
                    'maxWidth': '1060px', 'margin': '0 auto',
                }),
            ], style={'padding': '52px 48px 88px'}),
        ], style={'background': BG}),
    ], id='main-content'),

    _footer(),
], style={'fontFamily': 'Inter, -apple-system, sans-serif'})


# ── Active layout ──────────────────────────────────────────────────
app.layout = layout_a if LAYOUT == 'A' else layout_b
