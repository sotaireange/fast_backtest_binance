import numpy as np
import vectorbt as vbt
from numba import njit

from .registry import register_indicator

from src.app.indicators.standart import crossover,crossunder




@register_indicator('ohlc_indicator')
@njit
def ohlc_indicator(open: np.ndarray,
                   high: np.ndarray,
                   low: np.ndarray,
                   close: np.ndarray,
                   ema_len: int = 20,
                   rsi_len: int = 14,
                   rsi_buy: float = 30,
                   rsi_sell: float = 70,
                   flag_ema:bool=True,
                   flag_sma:bool=False):
    """
    OHLC Trading Indicator using RSI with EMA/SMA for buy/sell signal generation.

    This indicator combines Relative Strength Index (RSI) with either Exponential Moving Average (EMA)
    or Simple Moving Average (SMA) to generate trading signals based on trend direction and momentum.

    Parameters:
    -----------
    OHLC Data (MANDATORY np.ndarray type and this allowed names [open,high,low,close]) :
        open : np.ndarray
            Array of opening prices
        high : np.ndarray
            Array of high prices
        low : np.ndarray
            Array of low prices
        close : np.ndarray
            Array of closing prices

    Indicator Settings (any type allowed/any names):
        ema_len : int, default=20
            Period for EMA/SMA calculation
        rsi_len : int, default=14
            Period for RSI calculation
        rsi_buy : float, default=30
            RSI level for buy signals (oversold threshold)
        rsi_sell : float, default=70
            RSI level forsell signals (overbought threshold)

    Algorithm Selection Flags (flag_ prefix(any_names)):
        IMPORTANT: Only ONE flag can be True at a time!

        flag_ema : bool, default=True
            Use Exponential Moving Average for trend detection
        flag_sma : bool, default=False
            Use Simple Moving Average for trend detection

    Returns:
    --------
    tuple[np.ndarray, np.ndarray]
        buy : np.ndarray[bool]
            Boolean array indicating buy signals
        sell : np.ndarray[bool]
            Boolean array indicating sell signals

    Signal Logic:
    -------------
    EMA Mode (flag_ema=True):
        - Buy Signal: close[i] > ema[i] AND rsi[i] < rsi_buy
        - Sell Signal: close[i] < ema[i] AND rsi[i] > rsi_sell

    SMA Mode (flag_sma=True):
        - Buy Signal: close[i] > sma[i] AND rsi[i] < rsi_buy
        - Sell Signal: close[i] < sma[i] AND rsi[i] > rsi_sell

    Type Requirements:
    ------------------
    - OHLC parameters MUST be np.ndarray type
    - Parameters with 'flag_' prefix: Only one can be True (mutually exclusive)
    - Other boolean parameters: Can be True/False independently
    - Mandatory typing for all parameters

    Notes:
    ------
    - Function is compiled with @njit for high performance
    - Registered in indicator rфegistry as 'ohlc_indicator'
    - CRITICAL: Must always return (buy, sell) in this exact order
    - Uses vectorbt library for technical indicator calculations
    """

    n = len(close)

    buy = np.zeros(n, dtype=np.bool_)
    sell = np.zeros(n, dtype=np.bool_)


    # RSI
    delta = np.diff(close, prepend=close[0])
    gain = np.maximum(delta, 0)
    loss = np.maximum(-delta, 0)
    avg_gain = np.zeros(n)
    avg_loss = np.zeros(n)
    avg_gain[rsi_len-1] = np.mean(gain[:rsi_len])
    avg_loss[rsi_len-1] = np.mean(loss[:rsi_len])

    for i in range(rsi_len, n):
        avg_gain[i] = (avg_gain[i-1]*(rsi_len-1) + gain[i]) / rsi_len
        avg_loss[i] = (avg_loss[i-1]*(rsi_len-1) + loss[i]) / rsi_len

    rsi = np.zeros(n)
    for i in range(n):
        rs = avg_gain[i] / (avg_loss[i] + 1e-8)
        rsi[i] = 100 - 100/(1+rs)

    if flag_ema:
        ema = vbt.IndicatorFactory.from_ta('EMAIndicator').run(close, ema_len).ema_indicator

        for i in range(n):
            if close[i] > ema[i] and rsi[i] < rsi_buy:
                buy[i] = True
            if close[i] < ema[i] and rsi[i] > rsi_sell:
                sell[i] = True

    if flag_sma:
        sma=vbt.IndicatorFactory.from_ta('SMAIndicator').run(close, ema_len).sma_indicator
        for i in range(n):
            if close[i] > ema[i] and rsi[i] < rsi_buy:
                buy[i] = True
            if close[i] < ema[i] and rsi[i] > rsi_sell:
                sell[i] = True

    return buy, sell