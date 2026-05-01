from dash import html
from core.design_tokens import (
    PANEL, TEXT, MUTED, SUBTLE, BLUE,
    CARD_BORDER, CARD_SHADOW,
)


def _panel(children, flex=1, extra=None):
    s = {
        'background': PANEL,
        'borderRadius': '18px',
        'border': f'1px solid {CARD_BORDER}',
        'boxShadow': CARD_SHADOW,
        'overflow': 'hidden',
        'flex': str(flex),
        'minWidth': '0',
    }
    if extra:
        s.update(extra)
    return html.Div(children, style=s, className='dash-card')


def _ph(title, subtitle=''):
    return html.Div([
        html.H3(title, style={
            'fontSize': '15px', 'fontWeight': '600', 'color': TEXT,
            'letterSpacing': '-0.25px', 'lineHeight': '1.3', 'margin': '0',
        }),
        html.Div(subtitle, style={
            'fontSize': '11.5px', 'color': SUBTLE, 'marginTop': '3px',
            'fontWeight': '400', 'letterSpacing': '0px',
        }) if subtitle else '',
    ], style={'padding': '20px 20px 0'})


def _row(*children, gap='16px', mb='16px', className='ev-row'):
    return html.Div(list(children),
                    style={'display': 'flex', 'gap': gap, 'marginBottom': mb,
                           'flexWrap': 'wrap', 'alignItems': 'stretch'},
                    className=className)


def _legend_row(items):
    return html.Div([
        html.Div([
            html.Div(
                role='img',
                style={
                    'width': '8px', 'height': '8px', 'borderRadius': '50%',
                    'background': color, 'flexShrink': '0', 'marginTop': '3px',
                },
                **{'aria-label': f'{label} colour indicator'},
            ),
            html.Div([
                html.Span(label, style={'fontSize': '12px', 'color': TEXT, 'fontWeight': '500'}),
                html.Span(f'  {pct}', style={'fontSize': '12px', 'color': SUBTLE}),
            ]),
        ], style={'display': 'flex', 'alignItems': 'flex-start', 'gap': '8px'})
        for color, label, pct in items
    ], style={
        'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap',
        'padding': '10px 20px 18px',
    })


def _kpi(label, vid, did, accent=BLUE):
    return html.Div([
        html.Div(label, style={
            'fontSize': '10.5px', 'fontWeight': '600', 'color': SUBTLE,
            'textTransform': 'uppercase', 'letterSpacing': '0.7px',
        }),
        html.Div(
            id=vid,
            style={
                'fontSize': '2rem', 'fontWeight': '700', 'color': TEXT,
                'letterSpacing': '-0.8px', 'lineHeight': '1.1', 'marginTop': '12px',
                'fontVariantNumeric': 'tabular-nums',
            },
            **{'aria-live': 'polite', 'aria-atomic': 'true'},
        ),
        html.Div(
            id=did,
            style={
                'fontSize': '12px', 'color': MUTED, 'marginTop': '5px', 'fontWeight': '400',
            },
            **{'aria-live': 'polite', 'aria-atomic': 'true'},
        ),
        html.Div(
            style={
                'height': '2px', 'width': '24px', 'background': accent,
                'borderRadius': '2px', 'marginTop': '18px', 'opacity': '0.7',
            },
            **{'aria-hidden': 'true'},
        ),
    ], style={
        'background': PANEL,
        'borderRadius': '18px',
        'border': f'1px solid {CARD_BORDER}',
        'boxShadow': CARD_SHADOW,
        'padding': '22px 24px',
        'flex': '1',
        'minWidth': '160px',
    }, className='dash-card')


def _pill_label(text, label_id=None):
    style = {
        'fontSize': '10px', 'fontWeight': '600', 'color': SUBTLE,
        'textTransform': 'uppercase', 'letterSpacing': '0.7px', 'marginBottom': '7px',
    }
    return html.Div(text, id=label_id, style=style) if label_id else html.Div(text, style=style)
