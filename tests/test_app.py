import pytest
from unittest.mock import patch
import dash
from dash import html, dcc
from valuation_crypto.app import app, update_output

# Helper to recursively find components in layout
def find_component(layout, component_type, component_id=None):
    if isinstance(layout, component_type) and (component_id is None or getattr(layout, 'id', None) == component_id):
        return layout
    if hasattr(layout, 'children'):
        children = layout.children if isinstance(layout.children, list) else [layout.children]
        for child in children:
            found = find_component(child, component_type, component_id)
            if found:
                return found
    return None

# Mocked analysis data
@pytest.fixture
def mock_analysis_data():
    return {
        "current_price": 50000,
        "market_cap": 1000000000,
        "circulating_supply": 19000000,
        "velocity": 2.5,
        "sentiment_score": 0.1,
        "current_mentions": 100,
        "previous_mentions": 90,
        "adjusted_velocity": 2.75,
        "valuation_difference": 1000,
        "valuation_difference_percentage": 2.0,
        "market_sentiment_percentage": 10.0,
        "ai_text": "Mock AI Analysis Text"
    }

# Test Dash app initialization
def test_dash_app():
    assert isinstance(app, dash.Dash)
    assert app.title == "Crypto Valuation & Sentiment Analysis"

# Test Dash app layout
def test_dash_layout():
    layout = app.layout
    assert isinstance(layout, html.Div)

    input_field = find_component(layout, dcc.Input, "crypto-symbol")
    assert input_field is not None, "Crypto input field missing"

    analyze_button = find_component(layout, html.Button, "analyze-button")
    assert analyze_button is not None, "Analyze button missing"

    analysis_output = find_component(layout, html.Div, "analysis-output")
    assert analysis_output is not None, "Analysis output Div missing"

    price_velocity_graph = find_component(layout, dcc.Graph, "price-velocity-graph")
    assert price_velocity_graph is not None, "Price vs Velocity graph missing"

    sentiment_graph = find_component(layout, dcc.Graph, "sentiment-valuation-graph")
    assert sentiment_graph is not None, "Sentiment graph missing"

# Test Dash callback logic
@patch("valuation_crypto.utils.analyze_crypto")
def test_dash_callback(mock_analyze_crypto, mock_analysis_data):
    mock_analyze_crypto.return_value = (mock_analysis_data, "mock_image_url")

    outputs = update_output(1, "BTC")
    assert outputs is not None

    analysis_output, image_url, image_style, image_container_style, graph_container_style, sentiment_graph_container_style, fig1, fig2 = outputs

    # Check analysis output
    assert isinstance(analysis_output, html.Div)
    assert "Mock AI Analysis Text" in str(analysis_output)

    # Check image URL
    assert image_url == "mock_image_url"

    # Verify styles visibility
    assert image_style["display"] == "block"
    assert image_container_style["display"] == "flex"
    assert graph_container_style["display"] == "flex"
    assert sentiment_graph_container_style["display"] == "flex"

    # Verify graphs data
    assert fig1.data[0].x == (2.5,)
    assert fig1.data[0].y == (50000,)

    assert fig2.data[0].x == (0.1,)
    assert fig2.data[0].y == (1000,)
