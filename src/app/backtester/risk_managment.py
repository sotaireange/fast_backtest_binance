from typing import Tuple,Dict

import numpy as np
import pandas as pd
from numba import njit

from src.app.utils.config_loader import get_main_config,get_param_config
from src.app.strategies import get_strategy,get_indicator
from src.app.strategies.registry import get_list_names
from src.app.models import EntryExitResult,MainConfig

from vectorbt import IndicatorFactory
from vectorbt.indicators.factory import IndicatorBase
from src.common.loggers import get_logger



@njit
def _get_exits(close:np.ndarray,high:np.ndarray,low:np.ndarray,long_entries:np.ndarray,short_entries:np.ndarray,tp_pct:float,sl_pct:float) -> Tuple[np.ndarray,np.ndarray]:
    n_timestamps = long_entries.shape[0]
    n_combinations = long_entries.shape[1]

    long_exits = np.zeros_like(long_entries, dtype=np.bool_)
    short_exits= np.zeros_like(short_entries, dtype=np.bool_)
    for col_idx in range(n_combinations):
        entry_price_long = -1.0
        entry_price_short =-1.0
        long_col = long_entries[:, col_idx]
        short_col= short_entries[:,col_idx]

        for i in range(n_timestamps):
            if long_col[i] and entry_price_long < 0:
                entry_price_long = close[i]
                tp_level = entry_price_long * (1 + tp_pct)
                sl_level = entry_price_long * (1 - sl_pct)

                for j in range(i + 1, n_timestamps):
                    if high[j] >= tp_level:
                        long_exits[j, col_idx] = True
                        entry_price_long = -1.0
                        break
                    elif low[j] <= sl_level:
                        long_exits[j, col_idx] = True
                        entry_price_long = -1.0
                        break

            if short_col[i] and entry_price_short < 0:
                entry_price_short = close[i]
                tp_level = entry_price_short * (1 - tp_pct)
                sl_level = entry_price_short * (1 + sl_pct)

                for j in range(i + 1, n_timestamps):
                    if high[j] <= tp_level:
                        short_exits[j, col_idx] = True
                        entry_price_short = -1.0
                        break
                    elif low[j] >= sl_level:
                        short_exits[j, col_idx] = True
                        entry_price_short = -1.0
                        break


    return long_exits,short_exits
