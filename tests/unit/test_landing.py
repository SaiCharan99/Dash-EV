"""
Unit tests for landing/app.py layout structure.
Inspects the Dash component tree directly — no browser or server needed.
"""

import pytest
from dash import html


def _find_all(component, component_type, results=None):
    """Recursively collect all components of a given type in a layout tree."""
    if results is None:
        results = []
    if isinstance(component, component_type):
        results.append(component)
    children = getattr(component, 'children', None)
    if children is None:
        return results
    if isinstance(children, list):
        for child in children:
            _find_all(child, component_type, results)
    elif hasattr(children, 'children'):
        _find_all(children, component_type, results)
    return results


def _find_attrs(component, attr, value, results=None):
    """Find all components where component.<attr> == value."""
    if results is None:
        results = []
    if getattr(component, attr, None) == value:
        results.append(component)
    children = getattr(component, 'children', None)
    if isinstance(children, list):
        for child in children:
            _find_attrs(child, attr, value, results)
    elif children is not None and hasattr(children, 'children'):
        _find_attrs(children, attr, value, results)
    return results


@pytest.fixture(scope='module')
def layout():
    from landing.app import app
    return app.layout


class TestLandingLayout:
    def test_layout_is_html_div(self, layout):
        assert isinstance(layout, html.Div)

    def test_has_nav_bar(self, layout):
        # Nav is the first child; it contains "Energy" text
        spans = _find_all(layout, html.Span)
        texts = [s.children for s in spans if isinstance(s.children, str)]
        assert any('Energy' in t for t in texts)

    def test_has_platform_title(self, layout):
        h1s = _find_all(layout, html.H1)
        assert len(h1s) == 1
        assert 'Energy Intelligence Platform' in h1s[0].children

    def test_two_product_cards(self, layout):
        # Each card is an html.A linking to /ev/ and /energy/
        links = _find_all(layout, html.A)
        hrefs = [l.href for l in links if hasattr(l, 'href')]
        assert '/ev/' in hrefs
        assert '/energy/' in hrefs

    def test_ev_card_title(self, layout):
        # The EV card link wraps a Div with the title text
        links = _find_all(layout, html.A)
        ev_link = next((l for l in links if getattr(l, 'href', '') == '/ev/'), None)
        assert ev_link is not None
        divs = _find_all(ev_link, html.Div)
        texts = [d.children for d in divs if isinstance(d.children, str)]
        assert any('EV Market Intelligence' in t for t in texts)

    def test_energy_card_title(self, layout):
        links = _find_all(layout, html.A)
        energy_link = next((l for l in links if getattr(l, 'href', '') == '/energy/'), None)
        assert energy_link is not None
        divs = _find_all(energy_link, html.Div)
        texts = [d.children for d in divs if isinstance(d.children, str)]
        assert any('Australian Energy Transition' in t for t in texts)

    def test_footer_contains_data_sources(self, layout):
        divs = _find_all(layout, html.Div)
        all_text = ' '.join(str(d.children) for d in divs if isinstance(d.children, str))
        for source in ('AEMO', 'CSIRO', 'Dash'):
            assert source in all_text, f'Footer missing data source: {source}'

    def test_nav_has_data_sources_line(self, layout):
        divs = _find_all(layout, html.Div)
        all_text = ' '.join(str(d.children) for d in divs if isinstance(d.children, str))
        assert 'AEMO' in all_text


class TestProductCardHelper:
    """Tests the _product_card factory function directly."""

    def test_returns_html_a(self):
        from landing.app import _product_card
        from core.design_tokens import BLUE
        card = _product_card('Title', 'Sub', 'Desc', '/test/', BLUE, ['Tag1'])
        assert isinstance(card, html.A)

    def test_href_set(self):
        from landing.app import _product_card
        from core.design_tokens import GREEN
        card = _product_card('T', 'S', 'D', '/energy/', GREEN, [])
        assert card.href == '/energy/'

    def test_title_in_card(self):
        from landing.app import _product_card
        from core.design_tokens import BLUE
        card = _product_card('My Title', 'Sub', 'Desc', '/x/', BLUE, [])
        divs = _find_all(card, html.Div)
        texts = [d.children for d in divs if isinstance(d.children, str)]
        assert 'My Title' in texts

    def test_tags_rendered_as_spans(self):
        from landing.app import _product_card
        from core.design_tokens import BLUE
        card = _product_card('T', 'S', 'D', '/x/', BLUE, ['Tag A', 'Tag B', 'Tag C'])
        spans = _find_all(card, html.Span)
        tag_texts = [s.children for s in spans if isinstance(s.children, str)]
        assert 'Tag A' in tag_texts
        assert 'Tag B' in tag_texts

    def test_accent_color_in_top_stripe(self):
        from landing.app import _product_card
        accent = '#FF0000'
        card = _product_card('T', 'S', 'D', '/x/', accent, [])
        divs = _find_all(card, html.Div)
        stripe = next((d for d in divs if d.style and d.style.get('background') == accent
                       and d.style.get('height') == '4px'), None)
        assert stripe is not None, 'Top accent stripe not found'

    def test_no_text_decoration(self):
        from landing.app import _product_card
        from core.design_tokens import BLUE
        card = _product_card('T', 'S', 'D', '/x/', BLUE, [])
        assert card.style['textDecoration'] == 'none'
