"""
Unit tests for core/ shared design system.
Tests are pure-Python — no Dash server, no file I/O.
"""

import pytest
from core.design_tokens import (
    BG, PANEL, TEXT, SECONDARY, MUTED, SEP,
    BLUE, GREEN, ORANGE, RED, PURPLE, TEAL,
    PALETTE, ENERGY_SOLAR, ENERGY_WIND, ENERGY_COAL, ENERGY_GAS,
    ENERGY_HYDRO, ENERGY_BATT, ENERGY_SOURCE_COLORS, ENERGY_SOURCE_LABELS,
)
from core.chart_factory import _rgba, _chart, _dual_axis_chart, _bar_h
import plotly.graph_objects as go


# ── design_tokens ─────────────────────────────────────────────────────────────

class TestDesignTokens:
    def test_colors_are_hex(self):
        for name, val in [('BG', BG), ('PANEL', PANEL), ('TEXT', TEXT),
                          ('BLUE', BLUE), ('GREEN', GREEN)]:
            assert val.startswith('#'), f'{name} must be a hex color'
            assert len(val) in (4, 7), f'{name} hex must be 3 or 6 digits'

    def test_palette_has_at_least_six_colors(self):
        assert len(PALETTE) >= 6

    def test_palette_entries_are_hex(self):
        for c in PALETTE:
            assert c.startswith('#')

    def test_energy_source_colors_covers_all_sources(self):
        required = {
            'coal_black', 'coal_brown', 'gas_ccgt', 'gas_ocgt',
            'solar_utility', 'solar_rooftop', 'wind', 'hydro', 'battery_discharging',
        }
        assert required.issubset(ENERGY_SOURCE_COLORS.keys())

    def test_energy_source_labels_covers_all_sources(self):
        assert set(ENERGY_SOURCE_COLORS.keys()) == set(ENERGY_SOURCE_LABELS.keys())

    def test_energy_source_labels_are_strings(self):
        for k, v in ENERGY_SOURCE_LABELS.items():
            assert isinstance(v, str) and len(v) > 0, f'Empty label for {k}'


# ── chart_factory ─────────────────────────────────────────────────────────────

class TestRgba:
    def test_full_opacity(self):
        result = _rgba('#FF0000', 1.0)
        assert result == 'rgba(255,0,0,1.0)'

    def test_zero_opacity(self):
        result = _rgba('#000000', 0)
        assert result == 'rgba(0,0,0,0)'

    def test_mixed_color(self):
        result = _rgba('#1A2B3C', 0.5)
        assert result == 'rgba(26,43,60,0.5)'

    def test_strips_hash(self):
        a = _rgba('#FFFFFF', 1.0)
        b = _rgba('FFFFFF', 1.0)
        assert a == b


class TestChart:
    def test_returns_dict(self):
        layout = _chart()
        assert isinstance(layout, dict)

    def test_default_height(self):
        layout = _chart()
        assert layout['height'] == 320

    def test_custom_height(self):
        layout = _chart(height=500)
        assert layout['height'] == 500

    def test_has_required_keys(self):
        layout = _chart()
        for key in ('paper_bgcolor', 'plot_bgcolor', 'font', 'xaxis', 'yaxis', 'colorway'):
            assert key in layout, f'Missing key: {key}'

    def test_colorway_matches_palette(self):
        layout = _chart()
        assert layout['colorway'] == PALETTE


class TestDualAxisChart:
    def test_inherits_base_chart(self):
        layout = _dual_axis_chart()
        assert 'paper_bgcolor' in layout
        assert 'yaxis' in layout

    def test_has_yaxis2(self):
        layout = _dual_axis_chart()
        assert 'yaxis2' in layout
        assert layout['yaxis2']['overlaying'] == 'y'
        assert layout['yaxis2']['side'] == 'right'


class TestBarH:
    def test_returns_bar_trace(self):
        bar = _bar_h([1, 2, 3], ['A', 'B', 'C'], BLUE, '%{x}')
        assert isinstance(bar, go.Bar)

    def test_horizontal_orientation(self):
        bar = _bar_h([1, 2, 3], ['A', 'B', 'C'], BLUE, '%{x}')
        assert bar.orientation == 'h'

    def test_color_count_matches_bars(self):
        bar = _bar_h([1, 2, 3], ['A', 'B', 'C'], BLUE, '%{x}')
        assert len(bar.marker.color) == 3

    def test_last_bars_are_full_opacity(self):
        bar = _bar_h([1, 2, 3, 4, 5], ['A', 'B', 'C', 'D', 'E'], BLUE, '%{x}')
        colors = bar.marker.color
        assert colors[-1] == BLUE
        assert colors[-2] == BLUE
        assert colors[-3] == BLUE

    def test_early_bars_are_muted(self):
        bar = _bar_h([1, 2, 3, 4, 5], ['A', 'B', 'C', 'D', 'E'], '#FF0000', '%{x}')
        colors = bar.marker.color
        assert colors[0] != '#FF0000'
        assert 'rgba' in colors[0]

    def test_single_bar_full_opacity(self):
        bar = _bar_h([42], ['X'], GREEN, '%{x}')
        assert bar.marker.color[0] == GREEN
