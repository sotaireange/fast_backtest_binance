import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict,Tuple


from src.common.loggers import get_logger
from src.app.models import MainConfig,BackTestResult
from src.app.data.types import COLUMNS_RAW,COLUMNS_RESULT
from src.app.strategies.registry import get_strategy

log=get_logger('data_handler',False)

class CSVHandler:
    def __init__(self,config:MainConfig):
        self.config=config

    def _get_filepath_raw(self,coin:str) -> str:
        folder_path = Path('data/raw') / self.config.strategy.time.timeframe
        folder_path.mkdir(parents=True, exist_ok=True)
        return str(folder_path / f'{coin}.csv')


    def _get_filepath_result(self,coin:str) -> os.path:
        start_date=self.config.strategy.time.start_date.date()
        end_date=self.config.strategy.time.end_date.date()
        folder_path = Path('data/processed')/ f'{self.config.strategy.name}' / f'{start_date}_{end_date}' / self.config.strategy.time.timeframe
        folder_path.mkdir(parents=True, exist_ok=True)
        return str(folder_path / f'{coin}.csv')


    def get_or_empty_df(self,coin:str) -> pd.DataFrame:
        filepath=self._get_filepath_raw(coin)
        if os.path.exists(filepath):
            df= pd.read_csv(filepath,index_col='Open Time',parse_dates=True)
            df = df.sort_index()
            df = df[~df.index.duplicated(keep='first')]
            df = df.asfreq(pd.infer_freq(df.index))
            return df
        else:
            return pd.DataFrame(columns=COLUMNS_RAW)


    def get_df_with_datetime(self,coin:str,start:datetime,end:datetime) -> pd.DataFrame:
        df= self.get_or_empty_df(coin)
        df=df.loc[start:end]
        return df


    def get_result_or_empty_df(self,coin:str) -> pd.DataFrame:
        filepath=self._get_filepath_result(coin)
        if os.path.exists(filepath):
            df=pd.read_csv(filepath,index_col=[])
            param_cols = [col for col in df.columns if col.startswith(f"{self.config.strategy.name}_")]
            param_cols = [col for col in df.columns if col in param_cols]
            df = df.set_index(param_cols)
        else:
            params_names=[f'{self.config.strategy.name}_{param}' for param in get_strategy(self.config.strategy.name).param_names]
            index = pd.MultiIndex.from_arrays([[] for _ in params_names], names=params_names)
            df=pd.DataFrame(columns=COLUMNS_RESULT,index=index)
        return df

    def get_combination_done(self,coin:str) -> Optional[pd.MultiIndex]:
        df=self.get_result_or_empty_df(coin)
        if not df.empty:
            return df.index



    def save_raw_data(self, coin:str, df:pd.DataFrame):
        filepath=self._get_filepath_raw(coin)
        header=True
        mode='w'
        if os.path.exists(filepath):
            header=False
            mode='a'
        df.to_csv(filepath,index=True,mode=mode,header=header,index_label='Open Time')


    def save_result_to_csv(self, result: BackTestResult):
        filepath = self._get_filepath_result(result.coin)

        write_header = not (os.path.exists(filepath) and os.path.getsize(filepath) > 0)
        if (result.result is not None) and (not result.result.empty):
            result.result.to_csv(
                filepath,
                columns=COLUMNS_RESULT,
                mode='a',
                header=write_header,
            )




