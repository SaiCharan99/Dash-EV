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
        font=dict(family='Inter, -apple-system, sans-serif', color=TEXT, size=12),
        height=height,
        margin=dict(l=8, r=8, t=12, b=40),
        colorway=PALETTE,
        xaxis=dict(
            gridcolor='rgba(60,60,67,0.08)',
            linecolor='rgba(60,60,67,0.12)',
            zeroline=False, showgrid=True,
            tickfont=dict(color=MUTED, size=11),
            ticklen=0,
            title_font=dict(color=SECONDARY, size=11.5),
            title_standoff=10,
        ),
        yaxis=dict(
            gridcolor='rgba(60,60,67,0.08)',
            linecolor='rgba(60,60,67,0.12)',
            zeroline=False, showgrid=True,
            tickfont=dict(color=MUTED, size=11),
            ticklen=0,
            title_font=dict(color=SECONDARY, size=11.5),
            title_standoff=10,
        ),
        hoverlabel=dict(
            bgcolor=PANEL,
            bordercolor='rgba(60,60,67,0.15)',
            font=dict(color=TEXT, size=12.5, family='Inter, sans-serif'),
            namelength=-1,
        ),
        legend=dict(
            font=dict(color=SECONDARY, size=11.5),
            bgcolor='rgba(0,0,0,0)',
            orientation='h', yanchor='bottom', y=1.04, xanchor='right', x=1,
            itemsizing='constant', tracegroupgap=4,
            itemclick='toggleothers',
        ),
    )


def _dual_axis_chart(height=320):
    base = _chart(height)
    base['yaxis2'] = dict(
        overlaying='y', side='right',
        gridcolor='rgba(0,0,0,0)',
        zeroline=False,
        tickfont=dict(color=MUTED, size=11), ticklen=0,
        title_font=dict(color=SECONDARY, size=11.5),
        title_standoff=10,
    )
    return base


def _bar_h(x_vals, y_vals, color, hover_tmpl, min_alpha=0.22):
    n = len(y_vals)
    # linear fade: index 0 (shortest bar) → min_alpha, index n-1 (longest) → 1.0
    colors = [
        color if i == n - 1 else _rgba(color, min_alpha + (1.0 - min_alpha) * i / max(n - 1, 1))
        for i in range(n)
    ]
    return go.Bar(
        x=x_vals, y=y_vals, orientation='h',
        marker=dict(color=colors, line=dict(color='rgba(0,0,0,0)', width=0)),
        hovertemplate=hover_tmpl,
    )
