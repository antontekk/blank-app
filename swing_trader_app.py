import streamlit as st
import pandas as pd
import numpy as np
import websocket
import json
import threading
import time
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
from alpha_vantage.timeseries import TimeSeries
from streamlit_autorefresh import st_autorefresh

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame()
if 'last_price' not in st.session_state:
    st.session_state.last_price = None
if 'websocket' not in st.session_state:
    st.session_state.websocket = None

# Streamlit configuration
st.set_page_config(
    page_title="Real-time Swing Trade Analyzer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
    <style>
    .price-up { color: #00ff00; }
    .price-down { color: #ff0000; }
    .stAlert > div { background-color: #2b2b2b; }
    </style>
    """, unsafe_allow_html=True)

# Sidebar configuration
st.sidebar.title("Configuration")
ALPHA_VANTAGE_API_KEY = st.sidebar.text_input("Alpha Vantage API Key:", type="password")
symbol = st.sidebar.text_input("Enter Stock Symbol:", value="AAPL").upper()
update_interval = st.sidebar.slider("Update Interval (seconds):", 1, 60, 5)
lookback_period = st.sidebar.slider("Lookback Period (days):", 1, 30, 7)

# Auto refresh
st_autorefresh(interval=update_interval * 1000, key="datarefresh")

def fetch_historical_data(symbol):
    """Fetch historical data using Alpha Vantage API"""
    try:
        ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
        data, _ = ts.get_intraday(symbol=symbol, interval='1min', outputsize='full')
        data = data.sort_index()
        return data
    except Exception as e:
        st.error(f"Error fetching historical data: {str(e)}")
        return None

def calculate_indicators(df):
    """Calculate technical indicators"""
    if len(df) > 0:
        # RSI
        df['RSI'] = ta.momentum.RSIIndicator(df['4. close']).rsi()
        
        # MACD
        macd = ta.trend.MACD(df['4. close'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        
        # Bollinger Bands
        bollinger = ta.volatility.BollingerBands(df['4. close'])
        df['BB_Upper'] = bollinger.bollinger_hband()
        df['BB_Lower'] = bollinger.bollinger_lband()
        df['BB_Middle'] = bollinger.bollinger_mavg()
        
        # Volume SMA
        df['Volume_SMA'] = ta.volume.volume_sma_indicator(df['5. volume'])
        
        # ATR
        df['ATR'] = ta.volatility.AverageTrueRange(
            df['2. high'], df['3. low'], df['4. close']
        ).average_true_range()
        
        return df
    return None

def plot_charts(df):
    """Create interactive plotly charts"""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=('Price', 'RSI', 'MACD'),
        row_heights=[0.6, 0.2, 0.2]
    )

    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['1. open'],
            high=df['2. high'],
            low=df['3. low'],
            close=df['4. close'],
            name='OHLC'
        ),
        row=1, col=1
    )

    # Bollinger Bands
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], name='BB Upper', line=dict(color='gray', dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], name='BB Lower', line=dict(color='gray', dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Middle'], name='BB Middle', line=dict(color='gray', dash='dot')), row=1, col=1)

    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    # MACD
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], name='Signal', line=dict(color='orange')), row=3, col=1)

    fig.update_layout(
        title=f"{symbol} Real-time Analysis",
        height=800,
        xaxis_rangeslider_visible=False
    )

    return fig

def generate_signals(df):
    """Generate trading signals based on technical indicators"""
    signals = []
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # RSI Signals
    if latest['RSI'] < 30:
        signals.append(("STRONG BUY", "RSI oversold condition"))
    elif latest['RSI'] > 70:
        signals.append(("STRONG SELL", "RSI overbought condition"))
    
    # MACD Crossover
    if latest['MACD'] > latest['MACD_Signal'] and prev['MACD'] <= prev['MACD_Signal']:
        signals.append(("BUY", "MACD bullish crossover"))
    elif latest['MACD'] < latest['MACD_Signal'] and prev['MACD'] >= prev['MACD_Signal']:
        signals.append(("SELL", "MACD bearish crossover"))
    
    # Bollinger Bands
    if latest['4. close'] < latest['BB_Lower']:
        signals.append(("BUY", "Price below lower Bollinger Band"))
    elif latest['4. close'] > latest['BB_Upper']:
        signals.append(("SELL", "Price above upper Bollinger Band"))
    
    # Volume Analysis
    if latest['5. volume'] > latest['Volume_SMA'] * 1.5:
        signals.append(("ALERT", "High volume spike detected"))
    
    return signals

def display_metrics(df):
    """Display key metrics and statistics"""
    if len(df) > 0:
        latest = df.iloc[-1]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Current Price",
                f"${latest['4. close']:.2f}",
                f"{((latest['4. close'] - df.iloc[-2]['4. close']) / df.iloc[-2]['4. close'] * 100):.2f}%"
            )
        
        with col2:
            st.metric("RSI", f"{latest['RSI']:.2f}")
        
        with col3:
            st.metric(
                "MACD",
                f"{latest['MACD']:.2f}",
                f"{latest['MACD'] - latest['MACD_Signal']:.2f}"
            )
        
        with col4:
            st.metric("ATR", f"{latest['ATR']:.2f}")

def main():
    st.title("Real-time Swing Trade Analyzer")
    
    if not ALPHA_VANTAGE_API_KEY:
        st.warning("Please enter your Alpha Vantage API key in the sidebar.")
        return
    
    # Fetch initial historical data
    data = fetch_historical_data(symbol)
    if data is not None:
        # Calculate indicators
        data = calculate_indicators(data)
        
        # Display metrics
        display_metrics(data)
        
        # Plot charts
        st.plotly_chart(plot_charts(data), use_container_width=True)
        
        # Display signals
        signals = generate_signals(data)
        if signals:
            st.subheader("Trading Signals")
            for signal, reason in signals:
                if signal == "STRONG BUY":
                    st.success(f"🟢 {signal}: {reason}")
                elif signal == "STRONG SELL":
                    st.error(f"🔴 {signal}: {reason}")
                elif signal == "BUY":
                    st.info(f"↗️ {signal}: {reason}")
                elif signal == "SELL":
                    st.warning(f"↘️ {signal}: {reason}")
                else:
                    st.info(f"ℹ️ {signal}: {reason}")
        
        # Technical Analysis Summary
        st.subheader("Technical Analysis Summary")
        latest = data.iloc[-1]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Trend Indicators:**")
            st.write(f"• Price vs 20 MA: {'ABOVE' if latest['4. close'] > latest['BB_Middle'] else 'BELOW'}")
            st.write(f"• MACD Trend: {'BULLISH' if latest['MACD'] > latest['MACD_Signal'] else 'BEARISH'}")
        
        with col2:
            st.write("**Momentum Indicators:**")
            st.write(f"• RSI: {'OVERSOLD' if latest['RSI'] < 30 else 'OVERBOUGHT' if latest['RSI'] > 70 else 'NEUTRAL'}")
            st.write(f"• Volume Trend: {'HIGH' if latest['5. volume'] > latest['Volume_SMA'] else 'NORMAL'}")

if __name__ == "__main__":
    main()