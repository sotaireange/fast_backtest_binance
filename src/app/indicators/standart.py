import numpy as np
from numba import njit



@njit
def crossover(a:np.ndarray, b:np.ndarray) -> np.ndarray:
    out = np.full_like(a, False)
    for i in range(1, len(a)):
        if a[i] > b[i] and a[i - 1] <= b[i - 1]:
            out[i] = True
    return out

@njit
def crossunder(a:np.ndarray, b:np.ndarray) -> np.ndarray:
    out = np.full_like(a, False)
    for i in range(1, len(a)):
        if a[i] < b[i] and a[i - 1] >= b[i - 1]:
            out[i] = True
    return out

@njit
def ema(close:np.ndarray,window:int) -> np.ndarray:
    alpha = 2.0 / (window + 1.0)
    result = np.empty_like(close)
    result[0] = close[0]
    for i in range(1, len(close)):
        result[i] = alpha * close[i] + (1 - alpha) * result[i-1]

    return result