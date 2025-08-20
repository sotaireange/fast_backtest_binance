import pandas as pd
from pydantic import BaseModel,ConfigDict
from typing import Optional,List,Union
import numpy as np

class EntryExitResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    long_entries: pd.DataFrame
    short_entries: pd.DataFrame
    long_exits: Optional[np.ndarray] = None
    short_exits: Optional[np.ndarray] = None


class TpSlComb(BaseModel):
    tp: Union[float,List[float]]
    sl: Union[float,List[float]]

class CoinName(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    coin: str

class BackTestData(CoinName):
    df: pd.DataFrame


class BackTestResult(CoinName):
    result: Optional[pd.DataFrame]=None