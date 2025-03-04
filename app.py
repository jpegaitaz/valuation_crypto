import dash
from dash import dcc, html, Input, Output, State
import ccxt
import requests
import logging
import time
import random
from openai import OpenAI
import market_sentiment_reddit_gtrend
from apikey import cmc_api, openai_key

# Initialize OpenAI client
client = OpenAI(api_key=openai_key)

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Crypto Valuation & Analysis"

CMC_API_KEY = cmc_api
exchanges_list = ['binance', 'coinbasepro', 'kraken', 'bitfinex', 'huobi']

def fetch_trading_volume(crypto_symbol, exchanges_list):
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
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': CMC_API_KEY,
    }
    response = requests.get(url, headers=headers, params={'symbol': symbol, 'convert': 'USD'})
    if response.status_code == 200:
        data = response.json().get('data', {}).get(symbol, None)
        if data:
            return data
    return None

def analyze_crypto(symbol):
    crypto_data = fetch_crypto_data(symbol)
    if not crypto_data:
        return html.Div("Error: Invalid Crypto Symbol or Data Unavailable.", style={"color": "red", "font-weight": "bold"})

    crypto_id = crypto_data['name']
    crypto_symbol = crypto_data['symbol'].upper()
    current_price = round(crypto_data['quote']['USD']['price'], 2)
    market_cap = round(crypto_data['quote']['USD']['market_cap'], 2)
    circulating_supply = round(crypto_data.get('circulating_supply', 0), 2)

    total_volume_24h = fetch_trading_volume(crypto_symbol, exchanges_list)
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
            messages=[
                {"role": "system", "content": "You are a crypto data analyst"},
                {"role": "user", "content": prompt_text}
            ],
            max_tokens=300,
            temperature=0.7
        )
        analysis = chat_response.choices[0].message.content if chat_response.choices else "No valid response from ChatGPT."
    except Exception as e:
        analysis = f"⚠️ Error calling OpenAI: {e}"


    # Generate DALL-E Image
    try:
        image_prompt = f"Create an impactful related image, pixar like style. The image has to be impactful and humoristic, with a blénd of cartoonish and pop art like influence. The theme of the image are the events or annoucements related to {crypto_id} found on https://www.coindesk.com/," 
        f"Make sure the logo of {crypto_id} is included on the image"
        "Characters must be European origin"
        
        dalle_response = client.images.generate(
            model="dall-e-3",
            prompt=image_prompt,
            n=1,
            size="1024x1024"  
        )

        # Extracting Image URL
        image_url = dalle_response.data[0].url if dalle_response.data else None
    
        print(f"DALL-E Image URL: {image_url}")  

    except Exception as e:
        print(f"⚠️ DALL-E API Error: {e}")  
        image_url = None

    # Metrics Display
    metrics = f"""
    Ticker: {crypto_id} ({crypto_symbol})
    Price: ${current_price}
    Market Cap: ${market_cap}
    Circulating Supply: {circulating_supply}
    Velocity: {velocity}
    Sentiment Score: {combined_sentiment}
    Current Mentions: {current_mentions}
    Previous Mentions: {previous_mentions}
    Adjusted Velocity: {adjusted_velocity}
    Valuation Difference: {valuation_difference} ({valuation_difference_percentage}%)
    Market Sentiment %: {market_sentiment_percentage}
    """

    return html.Div([
        html.Div(metrics, style={"white-space": "pre-wrap", "font-family": "monospace", "padding": "10px"}),
        html.Hr(),
        html.H3("AI-Analysis"),
        html.Div(analysis, style={"white-space": "pre-wrap", "font-family": "monospace", "padding": "10px"})
    ]), image_url


# Dash App Layout
app.layout = html.Div(
    style={
        "background-color": "black",  
        "color": "white",  
        "min-height": "100vh",  
        "padding": "20px",
        "font-family": "Arial, sans-serif",
        "text-align": "center"
    },

    children=[
    html.H1("Crypto Valuation & Sentiment Analysis", style={"textAlign": "center", "color": "yellow", "font-family": "monospace"}),

    html.Div(
        children=[
            html.Img(
                id="crypto-image",
                src="",
                style={
                    "width": "512px",
                    "height": "512px",
                    "display": "block"
                }
            )
        ],
        style={
            "margin-bottom": "20px",
            "display": "flex", 
            "justify-content": "center",  
            "align-items": "center", 
            "text-align": "center"
        }
    ),

        html.Div(
            dcc.Input(
                id='crypto-symbol',
                type='text',
                placeholder='',
                style={
                    "width": "150px", "padding": "8px",
                    "border-radius": "10px", "background-color": "black",
                    "color": "white", "border": "1px solid white",
                    "text-align": "center",
                    "height":"50px",
                    "font-size":"50px"
                }
            ),
            style={"margin-bottom": "10px"}
        ),

        html.Div(
            html.Button(
                'Analyze', 
                id='analyze-button', 
                n_clicks=0,
                style={
                    "width": "100px", "padding": "10px",
                    "background-color": "red", "color": "white",
                    "border": "none", "border-radius": "5px",
                    "font-size": "16px", "font-weight": "bold",
                    "display": "block", "margin": "auto" 
                }
            ),
            style={"margin-bottom": "20px"}
        ),

        html.Div(
            id='analysis-output',
            style={"margin-top": "20px", "text-align": "left", "white-space": "pre-wrap", "padding-left": "500px", "padding-right":"500px", "padding-top":"20px"}
        )
    ]
)

# Callbacks
@app.callback(
    [Output('analysis-output', 'children'),
     Output('crypto-image', 'src'),
     Output('crypto-image', 'style')],
    Input('analyze-button', 'n_clicks'),
    State('crypto-symbol', 'value')
)

def update_output(n_clicks, symbol):
    if n_clicks > 0 and symbol and symbol.strip():
        analysis_output, image_url = analyze_crypto(symbol.strip().upper())

        image_style = {"width": "512px", "height": "512px", "display": "block"} if image_url else {"display": "none"}

        return analysis_output, image_url, image_style
    return "", "", {"display": "none"}

# Run Server
if __name__ == '__main__':
    app.run_server(debug=True)
