import pytest
from unittest.mock import patch, MagicMock
import dash
from dash import html, dcc
from valuation_crypto.app import app, update_output
from valuation_crypto import utils

# Helper function to find components by ID
def find_component(layout, component_id):
    if hasattr(layout, 'id') and layout.id == component_id:
        return layout
    if hasattr(layout, 'children'):
        children = layout.children if isinstance(layout.children, list) else [layout.children]
        for child in children:
            result = find_component(child, component_id)
            if result:
                return result
    return None

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

# Test Dash layout components
def test_dash_layout():
    layout = app.layout
    assert isinstance(layout, html.Div)

    # Debugging print statements
    print(f"DEBUG: Layout structure -> {layout}")

    assert find_component(layout, "crypto-symbol"), "Crypto input field missing"
    assert find_component(layout, "analyze-button"), "Analyze button missing"
    assert find_component(layout, "analysis-output"), "Analysis output missing"
    assert find_component(layout, "price-velocity-graph"), "Price-velocity graph missing"
    assert find_component(layout, "sentiment-valuation-graph"), "Sentiment-valuation graph missing"

# Test analyze_crypto utility
@patch("valuation_crypto.utils.fetch_crypto_data")
@patch("valuation_crypto.utils.fetch_trading_volume")
@patch("valuation_crypto.utils.market_sentiment_reddit_gtrend.aggregate_sentiment_analysis")
@patch("valuation_crypto.utils.client.chat.completions.create")
def test_analyze_crypto(mock_openai, mock_sentiment, mock_volume, mock_data, mock_analysis_data):
    mock_data.return_value = {
        'name': 'Bitcoin', 
        'symbol': 'BTC',
        'quote': {'USD': {'price': 50000, 'market_cap': 1000000000}},
        'circulating_supply': 19000000
    }
    mock_volume.return_value = 475000
    mock_sentiment.return_value = {'BTC': {'combined_sentiment_score': 0.1, 'current_mentions': 100, 'previous_mentions': 90}}
    mock_openai.return_value.choices = [MagicMock(message=MagicMock(content="Mock AI Analysis Text"))]

    result, img = utils.analyze_crypto("BTC")
    
    # Debugging prints
    print(f"DEBUG: analyze_crypto result -> {result}")

    assert result["current_price"] == 50000
    assert result["market_cap"] == 1000000000
    assert result["sentiment_score"] == 0.1
    assert "Mock AI Analysis Text" in result["ai_text"]

# Test Dash callback logic
@patch("valuation_crypto.utils.analyze_crypto")
def test_dash_callback(mock_analyze_crypto, mock_analysis_data):
    mock_analyze_crypto.return_value = (mock_analysis_data, "mock_image_url")

    outputs = update_output(1, "BTC")
    assert outputs is not None

    analysis_output, image_url, *_ = outputs

    # Debugging print statements
    print(f"DEBUG: Received analysis_output -> {analysis_output}")

    assert "Mock AI Analysis Text" in str(analysis_output)
    assert image_url == "mock_image_url"

# Test empty input callback
def test_dash_callback_empty_input():
    outputs = update_output(0, "")
    
    # Debugging print statements
    print(f"DEBUG: Empty input callback output -> {outputs}")

    assert outputs is not None
    assert outputs[0] == "", "Expected empty response when input is empty"

# Test invalid crypto symbol handling
@patch("valuation_crypto.utils.analyze_crypto")
def test_dash_callback_invalid_symbol(mock_analyze_crypto):
    mock_analyze_crypto.return_value = ({"error": "Invalid Crypto Symbol or Data Unavailable."}, None)

    outputs = update_output(1, "INVALID")
    
    # Debugging print statements
    print(f"DEBUG: Invalid symbol callback output -> {outputs}")

    assert outputs is not None
    analysis_output, image_url, *_ = outputs
    assert "Invalid Crypto Symbol or Data Unavailable." in str(analysis_output)
