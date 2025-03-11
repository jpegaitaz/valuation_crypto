import dash
from dash import dcc, html, Input, Output, State
from utils import analyze_crypto
import plotly.express as px

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Crypto Valuation & Sentiment Analysis"

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
        html.H1("CRYPTO VALUATION & SENTIMENT ANALYSIS", 
                style={"textAlign": "center", "color": "white", "font-family": "monospace", "font-size":"20px", "margin-bottom":"20px"}),

        # 🔹 **Image Display (Above Analysis)**
        html.Div(id="image-container",
            children=[html.Img(id="crypto-image", src="", 
                               style={"width": "512px", "height": "512px", "display": "none"})],
            style={"margin-bottom": "20px", "display": "flex", "justify-content": "center"}
        ),

        # 🔹 **Input Field**
        html.Div(
            dcc.Input(
                id='crypto-symbol',
                type='text',
                placeholder='',
                style={"width": "150px", "padding": "8px", "border-radius": "10px", 
                       "background-color": "black", "color": "white", 
                       "border": "1px solid white", "text-align": "center", 
                       "height": "50px", "font-size": "50px"}
            ),
            style={"margin-bottom": "10px"}
        ),

        # 🔹 **Analyze Button**
        html.Div(
            html.Button('Analyze', id='analyze-button', n_clicks=0,
                style={"width": "100px", "padding": "10px", "background-color": "red", 
                       "color": "white", "border": "none", "border-radius": "5px", 
                       "font-size": "16px", "font-weight": "bold", "display": "block", 
                       "margin": "auto", "margin-top":"25px"}
            ),
            style={"margin-bottom": "20px"}
        ),

        # 🔹 **AI Analysis Output (Metrics + AI Analysis Text)**
        html.Div(id='analysis-output',
            style={"margin-top": "20px", "text-align": "left", "white-space": "pre-wrap", 
                   "padding-left": "500px", "padding-right": "500px", "padding-top": "25px"}
        ),

        # 🔹 **Price vs Velocity Graph (Above)**
        html.Div(
            id="graph-container",
            children=[dcc.Graph(id="price-velocity-graph", 
                                style={"width": "425px", "height": "425px", 
                                       "border": "4px solid white", "margin-bottom": "20px"})],
            style={"display": "flex", "justify-content": "center", "margin-top": "20px"}
        ),

        # 🔹 **Sentiment Score vs Valuation Difference Graph (Below)**
        html.Div(
            id="sentiment-graph-container",
            children=[dcc.Graph(id="sentiment-valuation-graph", 
                                style={"width": "425px", "height": "425px", 
                                       "border": "4px solid white"})],
            style={"display": "flex", "justify-content": "center", "margin-top": "20px"}
        ),
    ]
)

@app.callback(
    [Output('analysis-output', 'children'),
     Output('crypto-image', 'src'),
     Output('crypto-image', 'style'),
     Output('image-container', 'style'),
     Output('graph-container', 'style'),
     Output('sentiment-graph-container', 'style'),
     Output('price-velocity-graph', 'figure'),
     Output('sentiment-valuation-graph', 'figure')],  # New output
    Input('analyze-button', 'n_clicks'),
    State('crypto-symbol', 'value')
)

def update_output(n_clicks, symbol):
    if n_clicks > 0 and symbol and symbol.strip():
        analysis_data, image_url = analyze_crypto(symbol.strip().upper())

        if "error" in analysis_data:
            return html.Div(analysis_data["error"], style={"color": "red", "font-weight": "bold"}), "", {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, px.scatter(), px.scatter()

        # 🔹 **Metrics Display**
        metrics_display = f"""
        - Ticker: {symbol.upper()}
        - Price: ${analysis_data['current_price']}
        - Market Cap: ${analysis_data['market_cap']}
        - Circulating Supply: {analysis_data['circulating_supply']}
        - Velocity: {analysis_data['velocity']}
        - Sentiment Score: {analysis_data['sentiment_score']}
        - Current Mentions: {analysis_data['current_mentions']}
        - Previous Mentions: {analysis_data['previous_mentions']}
        - Adjusted Velocity: {analysis_data['adjusted_velocity']}
        - Valuation Difference: {analysis_data['valuation_difference']} ({analysis_data['valuation_difference_percentage']}%)
        - Market Sentiment %: {analysis_data['market_sentiment_percentage']}
        """

        # 🔹 **AI Analysis Section**
        analysis_content = html.Div([
            html.Hr(),
            html.H3("Crypto Metrics"),
            html.Div(metrics_display, 
                     style={"white-space": "pre-wrap", "font-family": "monospace", "text-align": "left", "max-width": "550px", "margin-left": "auto", "margin-right": "auto"}),
            html.Hr(),
            html.H3("AI-Analysis"),
            html.Div(analysis_data['ai_text'], 
                     style={"white-space": "pre-wrap", "font-family": "monospace", "padding": "10px", "text-align": "left", "max-width": "550px", "margin-left": "auto", "margin-right": "auto"}),
            html.Hr()        
        ])

        # 🔹 **Generate Price vs. Velocity Graph**
        fig1 = px.scatter(
            x=[analysis_data['velocity']], 
            y=[analysis_data['current_price']],
            labels={"x": "Velocity", "y": "Price (USDT)"},
            title=f"{symbol.upper()} Price vs. Velocity",
            template="plotly_dark"
        )
        fig1.update_traces(marker=dict(size=12, color='yellow'))  # Highlight data point
        fig1.update_layout(
            font=dict(family="monospace", size=10),
            margin=dict(l=40, r=40, t=40, b=40),
            xaxis_title="Velocity (Annual Trading Volume / Circulating Supply)",
            yaxis_title="Price (USDT)"
        )

        # 🔹 **Generate Sentiment Score vs Valuation Difference Graph**
        fig2 = px.scatter(
            x=[analysis_data['sentiment_score']], 
            y=[analysis_data['valuation_difference']],
            labels={"x": "Sentiment Score", "y": "Valuation Difference (USDT)"},
            title=f"{symbol.upper()} Sentiment Score vs. Valuation Difference",
            template="plotly_dark"
        )
        fig2.update_traces(marker=dict(size=12, color='cyan'))  # Highlight data point
        fig2.update_layout(
            font=dict(family="monospace", size=10),
            margin=dict(l=40, r=40, t=40, b=40),
            xaxis_title="Sentiment Score",
            yaxis_title="Valuation Difference (USDT)"
        )

        # 🔹 **Ensure Image is Above AI Analysis**
        image_style = {"width": "512px", "height": "512px", "display": "block", "border": "4px solid white", "margin-top": "20px"} if image_url else {"display": "none"}
        image_container_style = {"display": "flex", "justify-content": "center", "margin-top": "20px", "margin-bottom": "20px"} if image_url else {"display": "none"}
        
        # ✅ Updated: Separate Graph Container Styles
        graph_container_style = {"display": "flex", "justify-content": "center", "margin-top": "20px", "margin-bottom": "20px"}  # Always visible
        sentiment_graph_container_style = {"display": "flex", "justify-content": "center", "margin-top": "20px"}  # Below the first graph

        return analysis_content, image_url, image_style, image_container_style, graph_container_style, sentiment_graph_container_style, fig1, fig2

    return "", "", {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, px.scatter(), px.scatter()

# 📌 **Run Server**
if __name__ == '__main__':
    app.run_server(debug=True)
