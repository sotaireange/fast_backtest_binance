import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict,Tuple


from src.common.loggers import get_logger
from src.app.models import MainConfig,BackTestResult
from src.app.data.types import COLUMNS_RAW,COLUMNS_RESULT,FormatDataReader
from src.app.strategies.registry import get_strategy
log=get_logger('data_handler',False)

class DataHandler:
    FORMAT=FormatDataReader.PARQUET
    FOLDER_PATH={'raw':'data/raw/','processed':'data/processed','analysis':'data/analysis'}

    def __init__(self,config:MainConfig):
        self.config=config
    def clean_multiindex_names(self,multiindex:pd.MultiIndex):
        current_names = multiindex.names

        new_names = []
        levels_to_keep = []

        for i, name in enumerate(current_names):
            if name and ('tp_stop' in name or 'sl_stop' in name):
                continue
            elif name and name.startswith(f'{self.config.strategy.name}_'):
                new_name = name.split('_',1)[1]
                new_names.append(new_name)
                levels_to_keep.append(i)
            else:
                new_names.append(name)
                levels_to_keep.append(i)

        multiindex_cleaned = multiindex.droplevel([i for i in range(len(current_names)) if i not in levels_to_keep])

        multiindex_cleaned.names = new_names

        return multiindex_cleaned

    def _get_filepath_raw(self,coin:str) -> str:
        folder_path = Path(self.FOLDER_PATH['raw']) / self.config.strategy.time.timeframe
        folder_path.mkdir(parents=True, exist_ok=True)
        return str(folder_path / f'{coin}.csv')

    def _get_folderpath_result(self) -> os.path:
        start_date=self.config.strategy.time.start_date.date()
        end_date=self.config.strategy.time.end_date.date()
        folder_path = Path(self.FOLDER_PATH['processed']) / f'{start_date}_{end_date}' / self.config.strategy.time.timeframe / f'{self.config.strategy.name}'
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path

    def _get_folderpath_analysis(self):
        start_date=self.config.strategy.time.start_date.date()
        end_date=self.config.strategy.time.end_date.date()
        folder_path = Path(self.FOLDER_PATH['analysis']) / f'{start_date}_{end_date}' / self.config.strategy.time.timeframe / f'{self.config.strategy.name}'
        folder_path.mkdir(parents=True, exist_ok=True)
        folder_path_symbol=folder_path / 'symbols'
        folder_path_symbol.mkdir(parents=True, exist_ok=True)
        return folder_path

    def _get_filepath_analysis(self,name:str,coin:bool):
        folder_path=self._get_folderpath_analysis()
        return str(folder_path / f'{name}.csv') if not coin else str(folder_path / 'symbols' / f'{name}.csv')

    def _get_filepath_result(self,coin:str) -> os.path:
        folder_path=self._get_folderpath_result()
        return str(folder_path / f'{coin}.{self.FORMAT}')


    def _get_all_symbol_in_folder(self) -> List[str]:
        folder_path=self._get_folderpath_result()
        return [file.stem for file in folder_path.glob(f"*.{self.FORMAT}")]


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


    def get_index_result_keys(self):
        return [f'{self.config.strategy.name}_{param}' for param in get_strategy(self.config.strategy.name).param_names]


    def get_df_with_datetime(self,coin:str,start:datetime,end:datetime) -> pd.DataFrame:
        df= self.get_or_empty_df(coin)
        df=df.loc[start:end]
        return df


    def get_result_or_empty_df(self,coin:str) -> pd.DataFrame:
        filepath=self._get_filepath_result(coin)
        if os.path.exists(filepath):
            if self.FORMAT==FormatDataReader.CSV:
                df=pd.read_csv(filepath,index_col=[])
                param_cols = self.get_index_result_keys() + ['tp_stop', 'sl_stop']
                df = df.set_index(param_cols)
            else:
                df=pd.read_parquet(filepath,engine='pyarrow')

        else:
            params_names=[f'{self.config.strategy.name}_{param}' for param in get_strategy(self.config.strategy.name).param_names]
            index = pd.MultiIndex.from_arrays([[] for _ in params_names], names=params_names)
            df=pd.DataFrame(columns=COLUMNS_RESULT,index=index)
        return df


    def get_all_result(self) -> pd.DataFrame:
        symbols=self._get_all_symbol_in_folder()
        all_dfs=[]
        for symbol in symbols:
            df=self.get_result_or_empty_df(symbol)
            df['symbol']=symbol
            df=df.set_index('symbol',append=True)
            all_dfs.append(df)
        return pd.concat(all_dfs).sort_index()



    def get_combination_done(self,coin:str) -> Optional[pd.MultiIndex]:
        df=self.get_result_or_empty_df(coin)
        if not df.empty:
            index=self.clean_multiindex_names(df.index)
            return index



    def save_raw_data(self, coin:str, df:pd.DataFrame):
        filepath=self._get_filepath_raw(coin)
        header=True
        mode='w'
        if os.path.exists(filepath):
            header=False
            mode='a'
        df.to_csv(filepath,index=True,mode=mode,header=header,index_label='Open Time')


    def save_result(self, result: BackTestResult):
        filepath = self._get_filepath_result(result.coin)

        write_header = not (os.path.exists(filepath) and os.path.getsize(filepath) > 0)
        if (result.result is not None) and (not result.result.empty):
            if self.FORMAT==FormatDataReader.CSV:
                result.result.to_csv(
                    filepath,
                    columns=COLUMNS_RESULT,
                    mode='a',
                    header=write_header,
                )
            else:
                filtered_data = result.result[COLUMNS_RESULT]

                if os.path.exists(filepath):
                    existing_data = pd.read_parquet(filepath, engine='pyarrow')
                    combined_data = pd.concat([existing_data, filtered_data], ignore_index=False)
                    combined_data.to_parquet(filepath, engine='pyarrow',index=combined_data.index)
                else:
                    filtered_data.to_parquet(filepath, engine='pyarrow',index=filtered_data.index)

    def save_analysis(self,df:pd.DataFrame,name:str,coin:bool=False):
        filepath=self._get_filepath_analysis(name,coin)
        df.to_csv(filepath,index=True,mode='w')
