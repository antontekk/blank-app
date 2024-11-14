# Default technical analysis parameters
DEFAULT_PERIODS = {
    'rsi': 14,
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'bb_period': 20,
    'volume_sma': 20
}

# Default risk management parameters
DEFAULT_RISK_PARAMS = {
    'stop_loss': 2.0,  # percentage
    'take_profit': 6.0,  # percentage
    'max_position_size': 5.0,  # percentage of portfolio
    'risk_per_trade': 1.0  # percentage of portfolio
}

# Time intervals available
TIME_INTERVALS = [
    '1min',
    '5min',
    '15min',
    '30min',
    '60min',
    'daily'
]

# UI Configuration
UI_THEME = {
    'DARK': {
        'bg_color': '#0e1117',
        'card_bg': '#1a1c23',
        'text_color': '#ffffff',
        'accent_color': '#00ff00'
    },
    'LIGHT': {
        'bg_color': '#ffffff',
        'card_bg': '#f0f2f6',
        'text_color': '#000000',
        'accent_color': '#00ab41'
    }
}

# Data source configuration
DATA_SOURCES = {
    'primary': 'alpha_vantage',
    'fallback': 'yahoo_finance'
}

# Update intervals (in seconds)
UPDATE_INTERVALS = {
    'real_time': 1,
    'fast': 5,
    'normal': 15,
    'slow': 60
}

# Alert settings
ALERT_TYPES = [
    'price_alert',
    'technical_signal',
    'volume_spike',
    'trend_change',
    'pattern_found'
]

# Notification settings
NOTIFICATION_SETTINGS = {
    'email': False,
    'browser': True,
    'sound': True
}