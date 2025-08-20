import asyncio
import pandas as pd
from binance import AsyncClient,Client
from binance.enums import HistoricalKlinesType
from datetime import datetime
import os
from typing import Union, List
import logging


from src.common.loggers import get_logger

from src.app.models import MainConfig
from src.app.data.types import COLUMNS_RAW,DataCoverage,DataRange
from src.app.data.csv_handler import CSVHandler





def get_symbols(config:MainConfig) -> List[str]:
    if config.strategy.symbols.use_all:
        client=Client()
        try:
            exchange_info=client.futures_exchange_info()
        finally:
            client.close_connection()
        symbols = [
            s['symbol']
            for s in exchange_info['symbols']
            if s['status'] == 'TRADING' and s['quoteAsset'] == 'USDT'
        ]
    else:
        symbols=config.strategy.symbols.symbols
    return symbols



class BinanceDataDownloader:
    def __init__(self,config: MainConfig):
        self.config=config
        self.data_handler=CSVHandler(config)


        logging.basicConfig(level=logging.INFO)
        self.logger = get_logger('downloader',False)

        self.tasks=[]

    async def __aenter__(self):
        self.client = await AsyncClient.create()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.close_connection()

    async def _get_symbols(self) -> List[str]:
        if self.config.strategy.symbols.use_all:
            exchange_info=await self.client.futures_exchange_info()
            symbols = [
                s['symbol']
                for s in exchange_info['symbols']
                if s['status'] == 'TRADING' and s['quoteAsset'] == 'USDT'
            ]
        else:
            symbols=self.config.strategy.symbols.symbols
        return symbols

    async def _download_klines(
            self,
            symbol: str,
            start_time: Union[str, datetime, int],
            end_time: Union[str, datetime, int],
    ) -> List:

        if not self.client:
            raise RuntimeError("Client not initialized")


        try:
            klines = await self.client.get_historical_klines(
                symbol=symbol,
                interval=self.config.strategy.time.timeframe,
                start_str=str(start_time),
                end_str=str(end_time),
                klines_type=HistoricalKlinesType.FUTURES
            )
            return klines

        except Exception as e:
            self.logger.error(f"Error donwload data: {e}")
            raise



    def klines_to_dataframe(self, klines: List) -> pd.DataFrame:
        if not klines:
            return pd.DataFrame()
        data = {
            'Open': [float(row[1]) for row in klines],
            'High': [float(row[2]) for row in klines],
            'Low': [float(row[3]) for row in klines],
            'Close': [float(row[4]) for row in klines],
            'Volume': [float(row[5]) for row in klines]
        }

        index = pd.to_datetime([float(row[0]) for row in klines], unit='ms')
        df = pd.DataFrame(data, index=index, dtype='float32')
        return df

    def get_df_coverage(self,symbol:str) -> List[DataRange]:
        df=self.data_handler.get_or_empty_df(symbol)

        dc=DataCoverage(time_start=self.config.strategy.time.start_date, time_end=self.config.strategy.time.end_date,
                        data_start=df.index.min() if not df.empty else None, data_end=df.index.max() if not df.empty else None
                        )
        return dc.get_overlap()


    async def download_and_save(
            self,
            symbol: str,
    ):

        data_coverages=self.get_df_coverage(symbol)
        for data_range in data_coverages:
            klines = await self._download_klines(
                symbol=symbol,
                start_time=data_range.start_time,
                end_time=data_range.end_time,
            )
            df = self.klines_to_dataframe(klines)
            if df.empty:
                self.logger.info('Take emtry DataFrame')
                continue

            self.data_handler.save_raw_data(symbol, df)


    async def download_multiple_symbols(
            self
    ):
        symbols=await self._get_symbols()
        for symbol in symbols:
            task=asyncio.create_task(self.download_and_save(symbol))
            await asyncio.sleep(0.5)
            self.tasks.append(task)

        await asyncio.gather(*self.tasks)