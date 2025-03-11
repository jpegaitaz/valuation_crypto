import pytest
from unittest.mock import patch, MagicMock
from valuation_crypto import utils

@pytest.fixture
def mock_crypto_data():
    return {
        "name": "Bitcoin",
        "symbol": "BTC",
        "quote": {"USD": {"price": 50000, "market_cap": 1000000000}},
        "circulating_supply": 19000000
    }

# ✅ Test fetching crypto data from API
@patch("valuation_crypto.utils.requests.get")
def test_fetch_crypto_data(mock_get, mock_crypto_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"BTC": mock_crypto_data}}
    mock_get.return_value = mock_response

    result = utils.fetch_crypto_data("BTC")

    assert result is not None, "Expected non-null response"
    assert result["name"] == "Bitcoin"
    assert result["symbol"] == "BTC"
    assert result["quote"]["USD"]["price"] == 50000

# ✅ Test API error handling
@patch("valuation_crypto.utils.requests.get")
def test_fetch_crypto_data_error(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404  # Simulating an invalid request
    mock_get.return_value = mock_response

    result = utils.fetch_crypto_data("BTC")

    assert result is None, "Expected None response for invalid API call"

# ✅ Test fetching trading volume from multiple exchanges
@patch("valuation_crypto.utils.ccxt.binance")
@patch("valuation_crypto.utils.ccxt.kraken")
def test_fetch_trading_volume(mock_binance, mock_kraken):
    mock_exchange_binance = MagicMock()
    mock_exchange_binance.load_markets.return_value = None
    mock_exchange_binance.symbols = ["BTC/USDT"]
    mock_exchange_binance.fetch_ticker.return_value = {"quoteVolume": 1500}

    mock_exchange_kraken = MagicMock()
    mock_exchange_kraken.load_markets.return_value = None
    mock_exchange_kraken.symbols = ["BTC/USD"]
    mock_exchange_kraken.fetch_ticker.return_value = {"quoteVolume": 2000}

    mock_binance.return_value = mock_exchange_binance
    mock_kraken.return_value = mock_exchange_kraken

    result = utils.fetch_trading_volume("BTC", ["binance", "kraken"])

    assert result == 3500, f"Expected 3500, got {result}"

# ✅ Test handling of missing trading volume
@patch("valuation_crypto.utils.ccxt.binance")
def test_fetch_trading_volume_no_data(mock_binance):
    mock_exchange = MagicMock()
    mock_exchange.load_markets.return_value = None
    mock_exchange.symbols = ["BTC/USDT"]
    mock_exchange.fetch_ticker.return_value = {}  # No volume key

    mock_binance.return_value = mock_exchange

    result = utils.fetch_trading_volume("BTC", ["binance"])

    assert result == 0, f"Expected 0, got {result}"

# ✅ Test `analyze_crypto` function
@patch("valuation_crypto.utils.fetch_crypto_data")
@patch("valuation_crypto.utils.fetch_trading_volume")
@patch("valuation_crypto.market_sentiment_reddit_gtrend.aggregate_sentiment_analysis")
@patch("valuation_crypto.utils.client.chat.completions.create")
@patch("valuation_crypto.utils.client.images.generate")
def test_analyze_crypto(mock_dalle, mock_chatgpt, mock_sentiment, mock_volume, mock_data, mock_crypto_data):
    mock_data.return_value = mock_crypto_data
    mock_volume.return_value = 5000
    mock_sentiment.return_value = {"BTC": {"combined_sentiment_score": 0.2, "current_mentions": 150, "previous_mentions": 100}}

    mock_chat_response = MagicMock()
    mock_chat_response.choices = [MagicMock(message=MagicMock(content="Mock OpenAI analysis"))]
    mock_chatgpt.return_value = mock_chat_response

    mock_dalle_response = MagicMock()
    mock_dalle_response.data = [MagicMock(url="mock_image_url")]
    mock_dalle.return_value = mock_dalle_response

    result, image_url = utils.analyze_crypto("BTC")

    assert result["current_price"] == 50000
    assert result["sentiment_score"] == 0.2
    assert result["ai_text"] == "Mock OpenAI analysis"
    assert image_url == "mock_image_url"

# ✅ Test handling of invalid crypto symbol in `analyze_crypto`
@patch("valuation_crypto.utils.fetch_crypto_data")
def test_analyze_crypto_invalid_symbol(mock_fetch):
    mock_fetch.return_value = None

    result, image_url = utils.analyze_crypto("INVALID")

    assert "error" in result, "Expected error message in response"
    assert image_url is None, "Expected None for invalid symbol image URL"

# ✅ Test OpenAI API failure handling
@patch("valuation_crypto.utils.fetch_crypto_data")
@patch("valuation_crypto.utils.fetch_trading_volume")
@patch("valuation_crypto.market_sentiment_reddit_gtrend.aggregate_sentiment_analysis")
@patch("valuation_crypto.utils.client.chat.completions.create", side_effect=Exception("OpenAI Error"))
def test_analyze_crypto_openai_failure(mock_chatgpt, mock_sentiment, mock_volume, mock_data, mock_crypto_data):
    mock_data.return_value = mock_crypto_data
    mock_volume.return_value = 5000
    mock_sentiment.return_value = {"BTC": {"combined_sentiment_score": 0.2, "current_mentions": 150, "previous_mentions": 100}}

    result, _ = utils.analyze_crypto("BTC")

    assert "OpenAI API Error" in result["ai_text"], "Expected OpenAI API failure message"

