import numpy as np
import pandas as pd
from numba import njit
import vectorbt as vbt
from vectorbt.indicators.factory import IndicatorFactory



@njit
def zero_lag(src:np.ndarray, length:int, gain_limit:int) -> np.ndarray:
    alpha = 2.0 / (length + 1)
    gain_factor = gain_limit / 10.0

    ema = np.full_like(src,0)
    ec = np.full_like(src,0)

    ema[0] = src[0]
    ec[0] = src[0]

    for i in range(1, len(src)):
        ema[i] = alpha * src[i] + (1 - alpha) * ema[i - 1]
        ec[i] = alpha * (ema[i] + gain_factor * (src[i] - ec[i - 1])) + (1 - alpha) * ec[i - 1]

    return ec


@njit
def aroon_oscillator(high:np.ndarray, low:np.ndarray, length:int,smooth:int, gain_limit:int) -> np.ndarray:
    n=len(high)
    aroon_up = np.full_like(high,0)
    aroon_down = np.full_like(high,0)

    for i in range(n):
        if i < length - 1:
            continue
        high_idx = np.argmax(high[i - length + 1:i + 1])
        low_idx = np.argmin(low[i - length + 1:i + 1])
        aroon_up[i] = 100.0 * (high_idx + 1) / length
        aroon_down[i] = 100.0 * (low_idx + 1) / length

    osc = aroon_up - aroon_down
    return zero_lag(osc, smooth, gain_limit)


@njit
def get_sig_line(close:np.ndarray,aroon_osc:np.ndarray,sign_len:int) -> np.ndarray:
    n=len(close)
    sig_line = np.empty_like(close)
    for i in range(sign_len - 1, n):
        window = aroon_osc[i - sign_len + 1:i + 1]
        sig_line[i] = np.sum(window) / len(window)
    for i in range(sign_len - 1):
        window = aroon_osc[0:i + 1]
        sig_line[i] = np.sum(window) / len(window)
    return sig_line


@njit
def get_zlma_side(close:np.ndarray,zlma:np.ndarray) -> np.ndarray:
    zlma_side = np.full_like(close, False, dtype=np.bool_)
    for i in range(3,len(close)):
        zlma_side[i] = zlma[i] > zlma[i - 3]
    return zlma_side