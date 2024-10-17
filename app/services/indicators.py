# app/services/indicators.py
import numpy as np
import pandas as pd

def simple_moving_average(data: pd.Series, period: int) -> pd.Series:
    return data.rolling(window=period).mean()

def exponential_moving_average(data: pd.Series, period: int) -> pd.Series:
    return data.ewm(span=period, adjust=False).mean()

def relative_strength_index(data: pd.Series, period: int) -> pd.Series:
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def bollinger_bands(data: pd.Series, period: int, num_std: float) -> pd.DataFrame:
    sma = simple_moving_average(data, period)
    std = data.rolling(window=period).std()
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    return pd.DataFrame({'middle': sma, 'upper': upper_band, 'lower': lower_band})

# Add more indicator calculations as needed