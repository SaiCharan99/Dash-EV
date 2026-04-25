from dash import html
from core.design_tokens import (
    PANEL, TEXT, SECONDARY, MUTED, SUBTLE, SEP, BLUE
)


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


def _row(*children, gap='16px', mb='16px', className='ev-row'):
    return html.Div(list(children),
                    style={'display': 'flex', 'gap': gap, 'marginBottom': mb,
                           'flexWrap': 'wrap', 'alignItems': 'stretch'},
                    className=className)


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
