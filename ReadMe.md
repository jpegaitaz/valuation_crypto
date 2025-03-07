![Build Status](https://github.com/jpegaitaz/valuation_crypto/actions/workflows/codeql.yml/badge.svg)[![Codacy Badge](https://app.codacy.com/project/badge/Grade/31d4d5d3746046599dd47dc8e0a66dff)](https://app.codacy.com/gh/jpegaitaz/valuation_crypto/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)[![Coverage Status](https://coveralls.io/repos/github/your_username/your_repo/badge.svg?branch=main)](https://coveralls.io/github/your_username/your_repo?branch=main)


# Crypto Valuation & Sentiment Analysis Dash App

## Overview
The **Crypto Valuation & Sentiment Analysis Dash App** is a web-based application built using **Dash, Flask, and CCXT** to analyze cryptocurrencies based on market data, sentiment analysis, and velocity calculations. The app integrates data from **CoinMarketCap, CCXT-supported exchanges, OpenAI GPT-4, and Reddit/Google Trends** to provide users with real-time insights into cryptocurrency valuation and sentiment trends.

## Features
- **Real-time Crypto Data Retrieval:** Fetches price, market cap, circulating supply, and trading volume data from **CoinMarketCap**.
- **Multi-Exchange Volume Aggregation:** Retrieves 24-hour trading volumes from multiple exchanges using **CCXT**.
- **Velocity Calculation:** Computes the annual trading volume and adjusts it based on sentiment analysis.
- **Sentiment Analysis:** Uses **Reddit & Google Trends** data to determine market sentiment for a cryptocurrency.
- **AI-Powered Analysis:** Utilizes **OpenAI GPT-4** to provide an expert opinion on the crypto market conditions based on extracted metrics.
- **DALL·E Image Generation:** Creates an AI-generated crypto-themed image based on market sentiment and news.
- **Interactive UI:** Built with Dash for an intuitive user experience.

## Installation
### Prerequisites
- Ensure you have **Python 3.8+** installed. Install dependencies using:
  ```sh
  pip install dash flask ccxt requests openai praw
  ```
- You will also need API keys for:
  - **CoinMarketCap API** (for price and market data)
  - **OpenAI API** (for AI-generated insights and DALL·E image generation)
  - **Reddit API** (for sentiment analysis)

### Setting Up API Keys
Create an `apikey.py` file and add:
```python
cmc_api = "YOUR_COINMARKETCAP_API_KEY"
openai_key = "YOUR_OPENAI_API_KEY"
reddit = praw.Reddit(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    user_agent="YOUR_USER_AGENT"
)
```

## Usage
1. **Run the app** using the command:
   ```sh
   python app.py
   ```
2. **Enter a cryptocurrency symbol** (e.g., BTC, ETH, SOL) in the input field.
3. **Click 'Analyze'** to generate real-time metrics, sentiment analysis, and AI-powered insights.
4. **View the AI-generated market analysis and image.**

## API Rate Limits & Handling
- The app includes **API rate-limiting protection** using **exponential backoff** and **response caching** to reduce unnecessary API calls.
- OpenAI API calls are cached for **5 minutes** to prevent excessive requests.

## Future Enhancements
- Implement **historical analysis** with trend forecasting.
- Add **more data sources** for sentiment analysis (e.g., Twitter, on-chain analytics).
- Improve **UI design** for better visualization of market trends.

## Contributing
Feel free to fork this repository and contribute improvements via pull requests.

## License
This project is licensed under the **MIT License**.
