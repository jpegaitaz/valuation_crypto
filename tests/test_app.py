import pytest
import dash
import requests
import valuation_crypto.app as app_module
import valuation_crypto.utils as utils
from unittest.mock import patch, MagicMock

# 🔹 Mock Crypto Data Fixture
@pytest.fixture
def mock_crypto_data():
    return {
        "name": "Bitcoin",
        "symbol": "BTC",
        "quote": {"USD": {"price": 50000, "market_cap": 1000000000}},
        "circulating_supply": 19000000
    }

# 🔹 Test: Fetch Crypto Data
@patch("valuation_crypto.utils.requests.get")  # ✅ Update import path
def test_fetch_crypto_data(mock_get, mock_crypto_data):
    """Test fetching crypto data from CoinMarketCap API"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"BTC": mock_crypto_data}}
    mock_get.return_value = mock_response

    result = utils.fetch_crypto_data("BTC")  # ✅ Call from utils.py
    
    assert result is not None
    assert result["name"] == "Bitcoin"
    assert result["symbol"] == "BTC"
    assert result["quote"]["USD"]["price"] == 50000


# 🔹 Test: Fetch Trading Volume (Mocking CCXT API)
@patch("valuation_crypto.utils.ccxt.binance")  # ✅ Update import path
@patch("valuation_crypto.utils.ccxt.kraken")
def test_fetch_trading_volume(mock_binance, mock_kraken):
    """Test trading volume retrieval across multiple exchanges"""
    mock_exchange = MagicMock()
    mock_exchange.fetch_ticker.return_value = {"quoteVolume": 1000}
    mock_binance.return_value = mock_exchange
    mock_kraken.return_value = mock_exchange

    result = utils.fetch_trading_volume("BTC", ["binance", "kraken"])  # ✅ Call from utils.py
    
    assert result == 2000 


# 🔹 Test: Analyze Crypto Data
@patch("valuation_crypto.utils.fetch_crypto_data")  # ✅ Update import path
@patch("valuation_crypto.utils.fetch_trading_volume")
@patch("valuation_crypto.utils.market_sentiment_reddit_gtrend.aggregate_sentiment_analysis")
def test_analyze_crypto(mock_sentiment, mock_volume, mock_data, mock_crypto_data):
    """Test analyze_crypto function with mocked API responses"""
    mock_data.return_value = mock_crypto_data
    mock_volume.return_value = 5000  
    mock_sentiment.return_value = {"BTC": {"combined_sentiment_score": 0.1, "current_mentions": 10, "previous_mentions": 5}}

    result, _ = utils.analyze_crypto("BTC")  # ✅ Call from utils.py
    
    assert "Ticker: Bitcoin (BTC)" in result.children[0].children 


# 🔹 Test: Dash App Loads Correctly
def test_dash_app():
    """Test Dash app initialization"""
    assert isinstance(app_module.app, dash.Dash)
    assert app_module.app.title == "Crypto Valuation & Sentiment Analysis"


# 🔹 Test: Dash Layout Contains Components
def test_dash_layout():
    """Test that Dash app layout contains the expected elements"""
    layout = app_module.app.layout
    assert isinstance(layout, dash.html.Div)

    # Ensure input field exists
    input_field = next((comp for comp in layout.children if isinstance(comp, dash.html.Div) and isinstance(comp.children, dash.dcc.Input)), None)
    assert input_field is not None, "Input field not found in layout"

    # Ensure button exists
    button = next((comp for comp in layout.children if isinstance(comp, dash.html.Div) and isinstance(comp.children, dash.html.Button)), None)
    assert button is not None, "Analyze button not found in layout"


# 🔹 Test: Dash Callback Execution
@patch("valuation_crypto.utils.analyze_crypto")  # ✅ Update import path
def test_dash_callback(mock_analyze_crypto):
    """Test Dash callback function"""
    mock_analyze_crypto.return_value = ("Mock Analysis", "mock_image_url")

    ctx = app_module.update_output(1, "BTC")
    
    assert ctx[0] == "Mock Analysis"
    assert ctx[1] == "mock_image_url"
