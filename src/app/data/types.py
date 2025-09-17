import pandas as pd
from pydantic import BaseModel,ConfigDict
from dataclasses import dataclass
from typing import Optional,List,Union,Dict
import numpy as np
from enum import Enum
from datetime import datetime

COLUMNS_RAW=['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume']
COLUMNS_RESULT=['Total Trades','Win Rate [%]','Total Return [%]']#, 'Max Drawdown [%]','Profit Factor','Sharpe Ratio']

metrics_info={'Start': 'start',
 'End': 'end',
 'Period': 'period',
 'Start Value': 'start_value',
 'End Value': 'end_value',
 'Total Return [%]': 'total_return',
 'Benchmark Return [%]': 'benchmark_return',
 'Max Gross Exposure [%]': 'max_gross_exposure',
 'Total Fees Paid': 'total_fees_paid',
 'Max Drawdown [%]': 'max_dd',
 'Max Drawdown Duration': 'max_dd_duration',
 'Total Trades': 'total_trades',
 'Total Closed Trades': 'total_closed_trades',
 'Total Open Trades': 'total_open_trades',
 'Open Trade PnL': 'open_trade_pnl',
 'Win Rate [%]': 'win_rate',
 'Best Trade [%]': 'best_trade',
 'Worst Trade [%]': 'worst_trade',
 'Avg Winning Trade [%]': 'avg_winning_trade',
 'Avg Losing Trade [%]': 'avg_losing_trade',
 'Avg Winning Trade Duration': 'avg_winning_trade_duration',
 'Avg Losing Trade Duration': 'avg_losing_trade_duration',
 'Profit Factor': 'profit_factor',
 'Expectancy': 'expectancy',
 'Sharpe Ratio': 'sharpe_ratio',
 'Calmar Ratio': 'calmar_ratio',
 'Omega Ratio': 'omega_ratio',
 'Sortino Ratio': 'sortino_ratio'}

METRICS=[metrics_info[key] for key in COLUMNS_RESULT]

@dataclass
class FormatDataReader:
    CSV='csv'
    PARQUET='parquet'


class Types(str, Enum):
    NONE=0 #do none
    BOTH=1 #do both
    UPPER=2 #do upper
    BOTTOM=3 #do bottom
    ALL=4 # do all


class DataRange(BaseModel):
    start_time: datetime
    end_time: datetime


class DataCoverage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    time_start: datetime
    time_end: datetime
    data_start: Optional[pd.Timestamp]=None
    data_end: Optional[pd.Timestamp]=None
    type: Optional[Types]=None

    no_overlap: List[DataRange]=[]


    def _get_types(self):
        if not self.data_start or not self.data_end:
            self.type=Types.ALL
            return


        if self.time_start<self.data_start and self.data_end<self.time_end:
            self.type=Types.BOTH
            return
        elif self.time_start>=self.data_start and self.data_end>=self.time_end:
            self.type=Types.NONE
            return
        if self.time_start<self.data_start:
            self.type=Types.BOTTOM
            return
        else:
            self.type=Types.UPPER
            return




    def get_overlap(self) -> List[DataRange]:
        self._get_types()
        if self.type in [Types.BOTTOM,Types.BOTH]:
            self.no_overlap.append(DataRange(start_time=self.time_start,end_time=self.data_start.to_pydatetime()))
        if self.type in [Types.UPPER,Types.BOTH]:
            self.no_overlap.append(DataRange(start_time=self.data_end.to_pydatetime(),end_time=self.time_end))
        if self.type==Types.ALL:
            self.no_overlap.append(DataRange(start_time=self.time_start,end_time=self.time_end))

        return self.no_overlap