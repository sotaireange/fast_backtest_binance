import pandas as pd
from pydantic import BaseModel,ConfigDict
from typing import Optional,List,Union,TypeVar
import numpy as np
import vectorbt as vbt

PortfolioT = TypeVar('PortfolioT', bound=vbt.Portfolio)


class EntryExitResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    long_entries: pd.DataFrame
    short_entries: Union[pd.DataFrame,np.ndarray,None]=None
    long_exits: Union[pd.DataFrame,np.ndarray,None]=None
    short_exits: Union[pd.DataFrame,np.ndarray,None]=None


class TpSlComb(BaseModel):
    tp: Union[float,List[float]]
    sl: Union[float,List[float]]

class TickerName(BaseModel): #TODO: Change to ticker/ TickerName
    model_config = ConfigDict(arbitrary_types_allowed=True)
    ticker: str

class BackTestData(TickerName):
    df: pd.DataFrame


class BackTestResult(TickerName):
    result: Optional[pd.DataFrame]=None
    pf: Optional[PortfolioT] = None