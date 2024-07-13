"""
Utility functions for the investment app.
"""
from alpha_vantage.timeseries import TimeSeries
from pycoingecko import CoinGeckoAPI

from core.constants import ALPHA_VANTAGE_API_KEY


def get_stock_price(symbol):
    """Get current price for a stock or bond using Alpha Vantage."""
    ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY)
    data, _ = ts.get_intraday(symbol=symbol, interval='5min', outputsize='compact')

    if "Time Series (5min)" in data:
        latest_timestamp = max(data["Time Series (5min)"].keys())
        latest_data = data["Time Series (5min)"][latest_timestamp]
        return float(latest_data['4. close'])
    else:
        raise KeyError(f"Key 'Time Series (5min)' not found in response: {data}")


def get_crypto_price(crypto_id):
    """Get current price for a cryptocurrency using CoinGecko."""
    cg = CoinGeckoAPI()
    data = cg.get_price(ids=crypto_id, vs_currencies='usd')
    if crypto_id in data:
        return data[crypto_id]['usd']
    else:
        raise ValueError(f"Price for {crypto_id} not found")


def get_current_price(investment_type, identifier):
    """Get current price based on investment type."""
    if investment_type == 'stock' or investment_type == 'bond':
        return get_stock_price(identifier)
    elif investment_type == 'cc':
        return get_crypto_price(identifier)
    else:
        raise ValueError(f"Unknown investment type {investment_type}.")