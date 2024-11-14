import pandas as pd
from alpha_vantage.timeseries import TimeSeries
import yfinance as yf
from datetime import datetime, timedelta

def fetch_stock_data(symbol, api_key, interval='1min', source='alpha_vantage'):
    """Fetch stock data from either Alpha Vantage or Yahoo Finance"""
    try:
        if source == 'alpha_vantage':
            ts = TimeSeries(key=api_key, output_format='pandas')
            if interval == 'daily':
                data, _ = ts.get_daily(symbol=symbol, outputsize='full')
            else:
                data, _ = ts.get_intraday(
                    symbol=symbol,
                    interval=interval,
                    outputsize='full'
                )
            data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        else:  # Yahoo Finance as fallback
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            data = yf.download(symbol, start=start_date, end=end_date, interval=interval)
        
        return data
    
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return None

def format_number(number, precision=2):
    """Format numbers for display"""
    if number >= 1_000_000_000:
        return f"{number/1_000_000_000:.{precision}f}B"
    elif number >= 1_000_000:
        return f"{number/1_000_000:.{precision}f}M"
    elif number >= 1_000:
        return f"{number/1_000:.{precision}f}K"
    else:
        return f"{number:.{precision}f}"

def calculate_change_percentage(current, previous):
    """Calculate percentage change"""
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

def get_trend_direction(data, periods=[20, 50]):
    """Determine trend direction using multiple moving averages"""
    trends = []
    close = data['Close'].iloc[-1]
    
    for period in periods:
        ma = data['Close'].rolling(window=period).mean().iloc[-1]
        trends.append(close > ma)
    
    if all(trends):
        return "Strong Uptrend"
    elif any(trends):
        return "Weak Uptrend"
    elif not any(trends):
        return "Strong Downtrend"
    else:
        return "Weak Downtrend"

def format_signal_message(signal):
    """Format trading signal messages"""
    strength_emoji = {
        'STRONG': '🔥',
        'MEDIUM': '⚡',
        'WEAK': '💡'
    }
    
    type_color = {
        'BUY': 'green',
        'SELL': 'red',
        'ALERT': 'yellow'
    }
    
    return {
        'emoji': strength_emoji.get(signal['strength'], ''),
        'color': type_color.get(signal['type'], 'white'),
        'message': f"{signal['indicator']}: {signal['reason']}"
    }