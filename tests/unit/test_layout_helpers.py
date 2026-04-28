"""
Unit tests for core/layout_helpers.py Dash component builders.
All assertions are on the Python component tree — no browser needed.
"""

import pytest
from dash import html
from core.layout_helpers import _panel, _ph, _row, _kpi, _legend_row, _pill_label
from core.design_tokens import PANEL, TEXT, BLUE, SUBTLE


# ── _panel ────────────────────────────────────────────────────────────────────

class TestPanel:
    def test_returns_html_div(self):
        result = _panel(html.Div('hello'))
        assert isinstance(result, html.Div)

    def test_default_flex_1(self):
        result = _panel('content')
        assert result.style['flex'] == '1'

    def test_custom_flex(self):
        result = _panel('content', flex=2)
        assert result.style['flex'] == '2'

    def test_flex_stored_as_string(self):
        result = _panel('content', flex=3)
        assert isinstance(result.style['flex'], str)

    def test_background_is_panel_color(self):
        result = _panel('x')
        assert result.style['background'] == PANEL

    def test_has_border_radius(self):
        result = _panel('x')
        assert 'borderRadius' in result.style

    def test_extra_styles_merged(self):
        result = _panel('x', extra={'color': 'red'})
        assert result.style.get('color') == 'red'
        assert 'borderRadius' in result.style

    def test_extra_can_override(self):
        result = _panel('x', extra={'background': '#123456'})
        assert result.style['background'] == '#123456'

    def test_children_passed_through(self):
        child = html.Span('test')
        result = _panel(child)
        assert result.children is child


# ── _ph ───────────────────────────────────────────────────────────────────────

class TestPh:
    def test_returns_html_div(self):
        assert isinstance(_ph('Title'), html.Div)

    def test_title_in_first_child(self):
        result = _ph('My Title')
        assert result.children[0].children == 'My Title'

    def test_no_subtitle_produces_empty_string(self):
        result = _ph('Title')
        assert result.children[1] == ''

    def test_subtitle_shown_when_provided(self):
        result = _ph('Title', 'Sub')
        assert isinstance(result.children[1], html.Div)
        assert result.children[1].children == 'Sub'

    def test_title_font_weight(self):
        result = _ph('Title')
        assert result.children[0].style['fontWeight'] == '600'

    def test_has_padding(self):
        result = _ph('Title')
        assert 'padding' in result.style


# ── _row ──────────────────────────────────────────────────────────────────────

class TestRow:
    def test_returns_html_div(self):
        assert isinstance(_row(), html.Div)

    def test_children_collected(self):
        a, b = html.Span('A'), html.Span('B')
        result = _row(a, b)
        assert len(result.children) == 2
        assert result.children[0] is a
        assert result.children[1] is b

    def test_default_gap(self):
        result = _row()
        assert result.style['gap'] == '16px'

    def test_custom_gap(self):
        result = _row(gap='24px')
        assert result.style['gap'] == '24px'

    def test_display_flex(self):
        result = _row()
        assert result.style['display'] == 'flex'

    def test_default_classname(self):
        result = _row()
        assert result.className == 'ev-row'

    def test_custom_classname(self):
        result = _row(className='en-row')
        assert result.className == 'en-row'


# ── _kpi ──────────────────────────────────────────────────────────────────────

class TestKpi:
    def test_returns_html_div(self):
        result = _kpi('Label', 'val-id', 'delta-id')
        assert isinstance(result, html.Div)

    def test_label_text_present(self):
        result = _kpi('Total TWh', 'v1', 'd1')
        assert result.children[0].children == 'Total TWh'

    def test_value_div_has_correct_id(self):
        result = _kpi('Label', 'my-val-id', 'my-delta-id')
        assert result.children[1].id == 'my-val-id'

    def test_delta_div_has_correct_id(self):
        result = _kpi('Label', 'v-id', 'd-id')
        assert result.children[2].id == 'd-id'

    def test_accent_color_applied(self):
        result = _kpi('Label', 'v', 'd', accent='#FF0000')
        accent_bar = result.children[3]
        assert accent_bar.style['background'] == '#FF0000'

    def test_default_accent_is_blue(self):
        result = _kpi('Label', 'v', 'd')
        accent_bar = result.children[3]
        assert accent_bar.style['background'] == BLUE

    def test_has_panel_background(self):
        result = _kpi('L', 'v', 'd')
        assert result.style['background'] == PANEL


# ── _legend_row ───────────────────────────────────────────────────────────────

class TestLegendRow:
    def test_returns_html_div(self):
        result = _legend_row([('#FF0000', 'Coal', '45%')])
        assert isinstance(result, html.Div)

    def test_one_item_per_entry(self):
        items = [('#F00', 'A', '10%'), ('#0F0', 'B', '20%'), ('#00F', 'C', '70%')]
        result = _legend_row(items)
        assert len(result.children) == 3

    def test_color_dot_uses_provided_color(self):
        result = _legend_row([('#ABCDEF', 'Wind', '30%')])
        dot = result.children[0].children[0]
        assert dot.style['background'] == '#ABCDEF'

    def test_label_text_present(self):
        result = _legend_row([('#000', 'Solar', '55%')])
        label_container = result.children[0].children[1]
        assert label_container.children[0].children == 'Solar'

    def test_pct_text_present(self):
        result = _legend_row([('#000', 'Solar', '55%')])
        label_container = result.children[0].children[1]
        assert '55%' in label_container.children[1].children

    def test_empty_list(self):
        result = _legend_row([])
        assert result.children == []


# ── _pill_label ───────────────────────────────────────────────────────────────

class TestPillLabel:
    def test_returns_html_div(self):
        assert isinstance(_pill_label('Year Range'), html.Div)

    def test_text_content(self):
        result = _pill_label('Region')
        assert result.children == 'Region'

    def test_uppercase_transform(self):
        result = _pill_label('season')
        assert result.style['textTransform'] == 'uppercase'

    def test_small_font(self):
        result = _pill_label('test')
        assert result.style['fontSize'] == '10px'
