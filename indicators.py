import pandas as pd
import numpy as np
import ta

def calculate_all_indicators(df, periods=None):
    """Calculate all technical indicators for the dataframe"""
    if periods is None:
        periods = {
            'rsi': 14,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'bb_period': 20
        }
    
    # RSI
    df['RSI'] = ta.momentum.RSIIndicator(
        df['Close'], 
        window=periods['rsi']
    ).rsi()
    
    # MACD
    macd = ta.trend.MACD(
        df['Close'],
        window_fast=periods['macd_fast'],
        window_slow=periods['macd_slow'],
        window_sign=periods['macd_signal']
    )
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Hist'] = macd.macd_diff()
    
    # Bollinger Bands
    bollinger = ta.volatility.BollingerBands(
        df['Close'],
        window=periods['bb_period']
    )
    df['BB_Upper'] = bollinger.bollinger_hband()
    df['BB_Middle'] = bollinger.bollinger_mavg()
    df['BB_Lower'] = bollinger.bollinger_lband()
    
    # Add Volume indicators
    df['Volume_SMA'] = ta.volume.volume_sma_indicator(
        df['Volume'],
        window=20
    )
    
    # Add trend indicators
    df['EMA_9'] = ta.trend.ema_indicator(df['Close'], window=9)
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
    
    return df

def generate_signals(df):
    """Generate trading signals based on technical indicators"""
    signals = []
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # RSI Signals
    if latest['RSI'] < 30:
        signals.append({
            'type': 'BUY',
            'strength': 'STRONG',
            'indicator': 'RSI',
            'reason': 'Oversold condition'
        })
    elif latest['RSI'] > 70:
        signals.append({
            'type': 'SELL',
            'strength': 'STRONG',
            'indicator': 'RSI',
            'reason': 'Overbought condition'
        })
    
    # MACD Crossover
    if (latest['MACD'] > latest['MACD_Signal'] and 
        prev['MACD'] <= prev['MACD_Signal']):
        signals.append({
            'type': 'BUY',
            'strength': 'MEDIUM',
            'indicator': 'MACD',
            'reason': 'Bullish crossover'
        })
    elif (latest['MACD'] < latest['MACD_Signal'] and 
          prev['MACD'] >= prev['MACD_Signal']):
        signals.append({
            'type': 'SELL',
            'strength': 'MEDIUM',
            'indicator': 'MACD',
            'reason': 'Bearish crossover'
        })
    
    # Bollinger Bands
    if latest['Close'] < latest['BB_Lower']:
        signals.append({
            'type': 'BUY',
            'strength': 'MEDIUM',
            'indicator': 'BB',
            'reason': 'Price below lower band'
        })
    elif latest['Close'] > latest['BB_Upper']:
        signals.append({
            'type': 'SELL',
            'strength': 'MEDIUM',
            'indicator': 'BB',
            'reason': 'Price above upper band'
        })
    
    # Volume Analysis
    if latest['Volume'] > latest['Volume_SMA'] * 1.5:
        signals.append({
            'type': 'ALERT',
            'strength': 'MEDIUM',
            'indicator': 'Volume',
            'reason': 'High volume spike'
        })
    
    return signals

def calculate_risk_metrics(df, risk_params):
    """Calculate risk metrics based on current position"""
    latest_price = df['Close'].iloc[-1]
    atr = ta.volatility.AverageTrueRange(
        df['High'],
        df['Low'],
        df['Close']
    ).average_true_range().iloc[-1]
    
    return {
        'stop_loss': latest_price * (1 - risk_params['stop_loss']/100),
        'take_profit': latest_price * (1 + risk_params['take_profit']/100),
        'atr': atr,
        'risk_reward_ratio': risk_params['take_profit'] / risk_params['stop_loss']
    }