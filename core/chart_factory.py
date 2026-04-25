import plotly.graph_objects as go
from core.design_tokens import (
    PANEL, TEXT, SECONDARY, MUTED, SUBTLE, SEP, PALETTE
)


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


def _dual_axis_chart(height=320):
    base = _chart(height)
    base['yaxis2'] = dict(
        overlaying='y', side='right',
        gridcolor='rgba(0,0,0,0)',
        zeroline=False,
        tickfont=dict(color=MUTED, size=11), ticklen=0,
        title_font=dict(color=SECONDARY, size=12),
    )
    return base


def _bar_h(x_vals, y_vals, color, hover_tmpl):
    n = len(y_vals)
    threshold = max(n - 3, 0)
    colors = [color if i >= threshold else _rgba(color, 0.38) for i in range(n)]
    return go.Bar(
        x=x_vals, y=y_vals, orientation='h',
        marker=dict(color=colors, line=dict(color='rgba(0,0,0,0)', width=0)),
        hovertemplate=hover_tmpl,
    )
