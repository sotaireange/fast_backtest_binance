import numpy as np
from numba import njit


@njit
def ma_calc(src: np.ndarray, volume: np.ndarray, length: int, ma_type: str) -> np.ndarray:
    if ma_type == "SMA":
        return sma(src, length)
    elif ma_type == "EMA":
        return ema(src, length)
    elif ma_type == "WMA":
        return wma(src, length)
    elif ma_type == "VWMA":
        return vwma(src, volume, length)
    elif ma_type == "RMA":
        return rma(src, length)
    else:
        return ema(src, length)

@njit
def vwma(src: np.ndarray, volume: np.ndarray, length: int) -> np.ndarray:
    result = np.empty_like(src)
    for i in range(length - 1, len(src)):
        pv = src[i - length + 1:i + 1] * volume[i - length + 1:i + 1]
        result[i] = np.sum(pv) / np.sum(volume[i - length + 1:i + 1])
    return result

@njit
def sma(src: np.ndarray, length: int) -> np.ndarray:
    result = np.full_like(src,np.inf)
    for i in range(length - 1, len(src)):
        result[i] = np.mean(src[i - length + 1:i + 1])
    return result
@njit
def ema(src: np.ndarray, length: int) -> np.ndarray:
    n=len(src)
    result = np.empty_like(src)
    if n == 0:
        return result
    alpha = 2.0 / (length + 1)
    result[0] = src[0]
    for i in range(1, n):
        result[i] = alpha * src[i] + (1.0 - alpha) * result[i - 1]
    return result

@njit
def wma(src: np.ndarray, length: int) -> np.ndarray:
    result = np.empty_like(src)
    weights = np.arange(1, length + 1)
    weight_sum = np.sum(weights)
    for i in range(length - 1, len(src)):
        result[i] = np.sum(src[i - length + 1:i + 1] * weights) / weight_sum
    return result



@njit
def rma(src: np.ndarray, length: int) -> np.ndarray:
    result = np.empty_like(src)
    alpha = 1.0 / length
    result[length - 1] = np.mean(src[:length])
    for i in range(length, len(src)):
        result[i] = alpha * src[i] + (1 - alpha) * result[i - 1]
    return result

@njit
def crossover(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    n = len(a)
    out = np.full_like(a,False, dtype=np.bool_)
    for i in range(1, n):
        if a[i] > b[i] and a[i - 1] <= b[i - 1]:
            out[i] = True
    return out

@njit
def crossunder(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    n = len(a)
    out = np.full_like(a,False, dtype=np.bool_)
    for i in range(1, n):
        if a[i] < b[i] and a[i - 1] >= b[i - 1]:
            out[i] = True
    return out

@njit
def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, length: int) -> np.ndarray:
    tr_arr = np.empty_like(high)
    tr_arr[0] = high[0] - low[0]
    for i in range(1, len(high)):
        tr1 = high[i] - low[i]
        tr2 = np.abs(high[i] - close[i - 1])
        tr3 = np.abs(low[i] - close[i - 1])
        tr_arr[i] = np.maximum(tr1, np.maximum(tr2, tr3))
    return rma(tr_arr, length)




@njit
def roc_calc(src: np.ndarray, length: int) -> np.ndarray:
    result = np.empty_like(src)
    for i in range(length, len(src)):
        result[i] = ((src[i] - src[i - length]) / src[i - length]) * 100
    return result

@njit
def highest(src: np.ndarray, length: int) -> np.ndarray:
    result = np.empty_like(src)
    for i in range(length - 1, len(src)):
        result[i] = np.max(src[i - length + 1:i + 1])
    return result


@njit
def lowest(src: np.ndarray, length: int) -> np.ndarray:
    result = np.empty_like(src)
    for i in range(length - 1, len(src)):
        result[i] = np.min(src[i - length + 1:i + 1])
    return result