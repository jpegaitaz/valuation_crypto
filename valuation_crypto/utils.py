import ccxt
import requests
from openai import OpenAI
from valuation_crypto.apikey import cmc_api, openai_key
import ccxt
import requests
from openai import OpenAI
from valuation_crypto import market_sentiment_reddit_gtrend  

# Initialize OpenAI client
client = OpenAI(api_key=openai_key)

CMC_API_KEY = cmc_api
exchanges_list = ['binance', 'coinbasepro', 'kraken', 'bitfinex', 'huobi']

def fetch_trading_volume(crypto_symbol, exchanges_list=exchanges_list):
    """Fetches total trading volume across multiple exchanges."""
    total_volume_24h = 0.0
    for exchange_id in exchanges_list:
        try:
            exchange = getattr(ccxt, exchange_id)()
            exchange.load_markets()
            pair = f"{crypto_symbol}/USDT" if f"{crypto_symbol}/USDT" in exchange.symbols else f"{crypto_symbol}/USD"
            ticker = exchange.fetch_ticker(pair)
            volume = ticker.get('quoteVolume', 0)
            total_volume_24h += volume
        except Exception:
            continue
    return round(total_volume_24h, 2)

def fetch_crypto_data(symbol):
    """Fetches crypto data from CoinMarketCap API."""
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': CMC_API_KEY,
    }
    response = requests.get(url, headers=headers, params={'symbol': symbol, 'convert': 'USD'})
    if response.status_code == 200:
        return response.json().get('data', {}).get(symbol, None)
    return None

def analyze_crypto(symbol):
    crypto_data = fetch_crypto_data(symbol)
    if not crypto_data:
        return {"error": "Invalid Crypto Symbol or Data Unavailable."}, None

    crypto_id = crypto_data['name']
    crypto_symbol = crypto_data['symbol'].upper()
    current_price = round(crypto_data['quote']['USD']['price'], 2)
    market_cap = round(crypto_data['quote']['USD']['market_cap'], 2)
    circulating_supply = round(crypto_data.get('circulating_supply', 0), 2)

    total_volume_24h = fetch_trading_volume(crypto_symbol)
    annual_trading_volume = total_volume_24h * 365
    velocity = round(annual_trading_volume / circulating_supply, 2) if circulating_supply else 0

    sentiment_data = market_sentiment_reddit_gtrend.aggregate_sentiment_analysis([(crypto_id, crypto_symbol)])
    sentiment = sentiment_data.get(crypto_symbol, {'combined_sentiment_score': 0, 'current_mentions': 0, 'previous_mentions': 0})
    
    combined_sentiment = sentiment['combined_sentiment_score']
    current_mentions = sentiment['current_mentions']
    previous_mentions = sentiment['previous_mentions']

    adjusted_velocity = round(velocity * (1 + combined_sentiment), 2)
    valuation_difference = round(adjusted_velocity - current_price, 2)
    valuation_difference_percentage = round((valuation_difference / current_price * 100), 2) if current_price else 0
    market_sentiment_percentage = round(((velocity - adjusted_velocity) / velocity * -1), 2) if velocity else 0

    # OpenAI Analysis
    prompt_text = (
        f"Below are recent metrics for {crypto_id} ({crypto_symbol}):\n"
        f"- Current Price: {current_price}\n"
        f"- Market Cap: {market_cap}\n"
        f"- Circulating Supply: {circulating_supply}\n"
        f"- Velocity: {velocity}\n"
        f"- Combined Sentiment Score: {combined_sentiment}\n"
        f"- Mentions: current={current_mentions}, previous={previous_mentions}\n"
        f"- Adjusted Velocity: {adjusted_velocity}\n"
        f"- Valuation Difference: {valuation_difference}\n"
        f"- Market Sentiment %: {market_sentiment_percentage}\n\n"
        "Comment briefly on these metrics in a fluid manner. "
        "Then, compare these data points with any recent news or articles published in the past few days about "
        f"{crypto_id} on https://www.coindesk.com/. Provide a very brief but fluent and concrete "
        "analysis showing how current events or announcements might be influencing the price, sentiment, "
        "and velocity metrics you see here."
        "Make sure by then end the final phrase is complete. Max. 300 tokens"
    )

    try:
        chat_response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are a crypto data analyst"},
                      {"role": "user", "content": prompt_text}],
            max_tokens=100,
            temperature=0.7
        )
        analysis = chat_response.choices[0].message.content if chat_response.choices else "No valid response from ChatGPT."
    except Exception as e:
        analysis = f"OpenAI API Error: {e}"

    # Generate DALL-E Image

    try:
        chat_response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are a crypto data analyst"},
                    {"role": "user", "content": prompt_text}],
            max_tokens=300,
            temperature=0.7
        )
        analysis = chat_response.choices[0].message.content if chat_response.choices else "No valid response from ChatGPT."
    except Exception as e:
        analysis = f"OpenAI API Error: {e}"

    # 🔹 **Determine Image Sentiment & Color Theme Based on Sentiment & Valuation**
    if combined_sentiment >= 0 and valuation_difference > 0:
        outlook = "highly optimistic, bullish market excitement"
        color_scheme = "warm, vibrant, and golden tones to reflect prosperity"
    elif combined_sentiment >= 0 and valuation_difference < 0:
        outlook = "cautiously optimistic, some skepticism remains"
        color_scheme = "neutral tones with hints of green and blue for mixed sentiment"
    elif combined_sentiment < 0 and valuation_difference > 0:
        outlook = "conflicted outlook, market uncertainty despite valuation strength"
        color_scheme = "contrasting elements with warm and cool tones to reflect hesitation"
    else:  # Both sentiment and valuation are negative
        outlook = "worst-case scenario, panic and fear dominate the market"
        color_scheme = "dark, chaotic, and stormy tones to emphasize extreme bearish sentiment"

    # 🔹 **Generate DALL-E Image**
    try:
        dalle_response = client.images.generate(
            model="dall-e-3",
            prompt=(
                f"Create a visually striking and engaging illustration in a Pixar-like style, incorporating elements of pop art and humor. "
                f"The image should reflect the overall market sentiment ({'positive' if combined_sentiment >= 0 else 'negative'}) "
                f"while integrating key themes from recent headlines or announcements about {crypto_id} on https://www.coindesk.com/. "
                f"Illustrate the mood of the crypto market by emphasizing {crypto_id}'s reaction to these events. "
                f"The image should metaphorically or symbolically represent how traders, investors, or the general public feel about {crypto_id}. "
                f"Current valuation analysis suggests a {outlook}. The color scheme should align with this sentiment: {color_scheme}. "
                f"Make sure the official logo of {crypto_id} is clearly visible in the artwork. "
                f"The characters depicted should have European facial features and be expressive to convey emotion effectively. "
                f"Ensure the image is high-resolution and suitable for a 1024x1024 pixel canvas."
            ),
            n=1,
            size="1024x1024"
        )
        image_url = dalle_response.data[0].url if dalle_response.data else None
    except Exception as e:
        print(f"DALL-E API Error: {e}")
        image_url = None

    return {
            "current_price": current_price,
            "market_cap": market_cap,
            "circulating_supply": circulating_supply,
            "velocity": velocity,
            "sentiment_score": combined_sentiment,
            "current_mentions": current_mentions,
            "previous_mentions": previous_mentions,
            "adjusted_velocity": adjusted_velocity,
            "valuation_difference": valuation_difference,
            "valuation_difference_percentage": valuation_difference_percentage,
            "market_sentiment_percentage": market_sentiment_percentage,
            "ai_text": analysis
        }, image_url