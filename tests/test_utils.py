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

@patch("valuation_crypto.utils.requests.get")
def test_fetch_crypto_data(mock_get, mock_crypto_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"BTC": mock_crypto_data}}
    mock_get.return_value = mock_response

    result = utils.fetch_crypto_data("BTC")

    assert result is not None
    assert result["name"] == "Bitcoin"
    assert result["symbol"] == "BTC"


@patch("valuation_crypto.utils.ccxt.binance")
@patch("valuation_crypto.utils.ccxt.kraken")
def test_fetch_trading_volume(mock_binance, mock_kraken):
    mock_exchange = MagicMock()
    mock_exchange.load_markets.return_value = None
    mock_exchange.symbols = ["BTC/USDT"]
    mock_exchange.fetch_ticker.return_value = {"quoteVolume": 1500}

    mock_binance.return_value = mock_exchange
    mock_kraken.return_value = mock_exchange

    result = utils.fetch_trading_volume("BTC", ["binance", "kraken"])

    assert result == 3000


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
