import pytest
from unittest.mock import patch, MagicMock
import dash
from dash import html, dcc
from valuation_crypto.app import app, update_output
from valuation_crypto import utils

def find_component(component, component_id):
    """
    Recursively search for a Dash component by its ID within the layout.
    Prints debug info so we can see if we found a match or if we keep going.
    """
    if hasattr(component, "id"):
        print(f"DEBUG find_component: Checking component with id = {component.id!r}")
        if component.id == component_id:
            print(f"DEBUG find_component: Found match for {component_id}")
            return component

    if hasattr(component, "children"):
        children = component.children
        if not isinstance(children, list):
            children = [children]
        for child in children:
            found = find_component(child, component_id)
            if found:
                return found

    return None

@pytest.fixture
def mock_analysis_data():
    """Fixture to return mock analysis data for testing."""
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

@pytest.fixture(scope="module")
def static_layout():
    """Returns a 'frozen' version of app.layout."""
    return app.layout

def test_dash_app():
    assert isinstance(app, dash.Dash)
    assert app.title == "Crypto Valuation & Sentiment Analysis"

def test_dash_layout(static_layout):
    """
    Check that all key components exist in the Dash layout.
    We use the static_layout fixture to avoid multiple re-calls of app.layout.
    """
    layout = static_layout
    assert isinstance(layout, html.Div)

    print(f"\nDEBUG: Layout structure -> {layout}")

    component_ids = [
        "crypto-symbol",
        "analyze-button",
        "analysis-output",
        "price-velocity-graph",
        "sentiment-valuation-graph"
    ]
    found_results = {}
    for cid in component_ids:
        component = find_component(layout, cid)
        found_results[cid] = component
        print(f"DEBUG test_dash_layout: For {cid}, find_component returned => {component}")

    missing_components = [cid for cid, comp in found_results.items() if comp is None]
    print(f"\nDEBUG test_dash_layout: Final 'found_results' => {found_results}")
    assert not missing_components, f"Missing components: {missing_components}"

@patch("valuation_crypto.utils.fetch_crypto_data")
@patch("valuation_crypto.utils.fetch_trading_volume")
@patch("valuation_crypto.market_sentiment_reddit_gtrend.aggregate_sentiment_analysis")
@patch("valuation_crypto.utils.client.chat.completions.create")
def test_analyze_crypto(mock_openai, mock_sentiment, mock_volume, mock_data, mock_analysis_data):
    """Mock API calls and test analyze_crypto function."""
    mock_data.return_value = {
        'name': 'Bitcoin',
        'symbol': 'BTC',
        'quote': {'USD': {'price': 50000, 'market_cap': 1000000000}},
        'circulating_supply': 19000000
    }
    mock_volume.return_value = 475000
    mock_sentiment.return_value = {
        'BTC': {
            'combined_sentiment_score': 0.1,
            'current_mentions': 100,
            'previous_mentions': 90
        }
    }
    mock_openai.return_value.choices = [
        MagicMock(message=MagicMock(content="Mock AI Analysis Text"))
    ]

    result, img = utils.analyze_crypto("BTC")
    print(f"\nDEBUG: analyze_crypto result -> {result}")

    assert result["current_price"] == 50000
    assert result["market_cap"] == 1000000000
    assert result["sentiment_score"] == 0.1
    assert "Mock AI Analysis Text" in result["ai_text"]

@patch("valuation_crypto.app.analyze_crypto")
def test_dash_callback(mock_analyze_crypto, mock_analysis_data):
    """Test callback with mocked analysis data."""
    mock_analyze_crypto.return_value = (mock_analysis_data, "mock_image_url")
    outputs = update_output(1, "BTC")
    assert outputs is not None

    analysis_output, image_url, *_ = outputs
    print(f"\nDEBUG: Received analysis_output -> {analysis_output}")
    assert "Mock AI Analysis Text" in str(analysis_output), (
        f"Expected 'Mock AI Analysis Text', but got: {analysis_output}"
    )
    assert image_url == "mock_image_url"

def test_dash_callback_empty_input():
    """Test callback with empty input (should return empty response)."""
    outputs = update_output(0, "")
    print(f"\nDEBUG: Empty input callback output -> {outputs}")
    assert outputs is not None
    assert outputs[0] == "", "Expected empty response when input is empty"

@patch("valuation_crypto.app.analyze_crypto")
def test_dash_callback_invalid_symbol(mock_analyze_crypto):
    """Test callback with invalid crypto symbol."""
    mock_analyze_crypto.return_value = (
        {"error": "Invalid Crypto Symbol or Data Unavailable."},
        None
    )
    outputs = update_output(1, "INVALID")
    print(f"\nDEBUG: Invalid symbol callback output -> {outputs}")

    assert outputs is not None
    analysis_output, image_url, *_ = outputs
    assert "Invalid Crypto Symbol or Data Unavailable." in str(analysis_output), (
        "Expected error message for invalid symbol"
    )
