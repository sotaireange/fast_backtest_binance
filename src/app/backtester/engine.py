from typing import Tuple,Dict,List,Union,Optional
import os
from multiprocessing.managers import DictProxy


import numpy as np
import pandas as pd
import logging
import vectorbt as vbt

from src.app.backtester.risk_managment import _get_exits
from src.app.utils.config_loader import get_param_config
from src.app.strategies import get_strategy
from src.app.models import EntryExitResult,MainConfig,TpSlComb,BackTestResult,BackTestData
from src.app.backtester.combination_generation import ParamCombinationsGenerator
from src.app.data.downloader import get_symbols
from src.app.utils.helpers import chunkify
from src.app.data.csv_handler import DataHandler
from src.common.loggers import get_logger


logger=get_logger('backtester',False)




class MultiParamPortfolioBacktest: #TODO: MEMORY LEAK Нужно будет решить эту проблему, когда tp_sl комбинация

    def __init__(self, config:MainConfig,pid:int=0,symbols:Optional[List[str]]=None,progress_dict:Optional[DictProxy]=None):
        self.config:MainConfig=config
        self.data_handler=DataHandler(config)
        self.params=get_param_config(config.strategy.name)
        self.indicator=get_strategy(config.strategy.name)
        self.params_comb=ParamCombinationsGenerator(self.params)
        self.progress_dict=progress_dict if progress_dict else {}
        self.symbols=symbols if symbols else self.config.strategy.symbols.symbols
        self.pid=pid

    def _get_entries(self,params:Dict,**kwargs) -> Tuple[pd.DataFrame,pd.DataFrame,pd.MultiIndex]:
        kwargs = {k: v for k, v in kwargs.items() if k in self.indicator.input_names}
        result=tuple()
        try:
            result=self.indicator.run(**kwargs,
                                      **params,
                                      param_product=False)
        except Exception as e:
            logger.exception('Eror in _get_entries)')
        if not result: return result
        if isinstance(result.buy, pd.Series):
            return result.buy.to_frame(), result.sell.to_frame(), result.buy.to_frame().columns
        return result.buy,result.sell,result.buy.columns

    def _get_exits(self,long_entries:np.ndarray,short_entries:np.ndarray,**kwargs:np.ndarray) -> Tuple[np.ndarray,np.ndarray]:
        try:
            close = kwargs['close']
            high = kwargs['high']
            low = kwargs['low']
        except KeyError as e:
            raise ValueError(f"Missing required price array in kwargs: {e}")
        exits = tuple()
        try:
            exits=_get_exits(
                close=close,
                high=high,
                low=low,
                long_entries=long_entries,
                short_entries=short_entries,
                tp_pct=self.config.strategy.size.tp_pct.fix,
                sl_pct=self.config.strategy.size.sl_pct.fix
            )
        except Exception as e:
            logger.exception('Erro in _get_exits')
        finally:

            return exits



    def _get_entries_and_exists(self,params:Dict,**kwargs) -> EntryExitResult:
        long_entries,short_entries,columns=self._get_entries(params,**kwargs)
        if self.config.strategy.size.use_only_tp_sl:
            long_exits = None
            short_exits = None
        else:
            long_exits, short_exits = self._get_exits(
                long_entries=long_entries.values,
                short_entries=short_entries.values,
                **kwargs
            )
        return EntryExitResult(long_entries=long_entries,
                               short_entries=short_entries,
                               long_exits=long_exits,
                               short_exits=short_exits,
                               index=columns)

    def _get_tp_sl(self,entry_exits:EntryExitResult) -> Tuple[EntryExitResult,TpSlComb]:
        entries=entry_exits.long_entries
        short_entries=entry_exits.short_entries
        long_exits=entry_exits.long_exits
        short_exits=entry_exits.short_exits

        tp_sl_index=self.config.strategy.size.get_combinations()
        multi_index = pd.MultiIndex.from_tuples(
            [param + sltp for param in entries.columns for sltp in tp_sl_index],
            names=entry_exits.long_entries.columns.names +tp_sl_index.names
        )
        entries_expanded = pd.concat([entries] * len(tp_sl_index), axis=1)
        short_entries_expanded = pd.concat([short_entries] * len(tp_sl_index), axis=1)
        if long_exits is not None:
            exits_expanded = pd.concat([long_exits] * len(tp_sl_index), axis=1)
            short_exits_expanded = pd.concat([short_exits] * len(tp_sl_index), axis=1)
            exits_expanded.columns = multi_index
            short_exits_expanded.columns = multi_index
            entry_exits.long_exits=exits_expanded
            entry_exits.short_exits=short_exits_expanded
        entries_expanded.columns = multi_index
        short_entries_expanded.columns = multi_index
        entry_exits.long_entries=entries_expanded
        entry_exits.short_entries=short_entries_expanded
        tp_values = [tp for _ in entries.columns for sl, tp in tp_sl_index]
        sl_values = [sl for _ in entries.columns for sl, tp in tp_sl_index]
        return entry_exits,TpSlComb(tp=tp_values,sl=sl_values)

    def _combination_via_tp_sl(self,df:pd.DataFrame,entry_exits:EntryExitResult) -> pd.DataFrame:
        dfs=[]
        tp_sl_index=self.config.strategy.size.get_combinations()
        for tp,sl in tp_sl_index:
            stats=self.run_portfolio(df,entry_exits,TpSlComb(tp=tp,sl=sl))
            stats.index = pd.MultiIndex.from_tuples(
                [idx + (sl, tp)  for idx in stats.index],
                names=stats.index.names + ['sl_stop', 'tp_stop']
            )
            dfs.append(stats)
        return pd.concat(dfs)


    def _prepare_njit(self,data:BackTestData,params:dict):
        entry_exits=self._get_entries_and_exists(params,close=data.df['Close'].values,
                                                 open=data.df['Open'].values,
                                                 high=data.df['High'].values,
                                                 low=data.df['Low'].values,
                                                 volume=data.df['Volume'].values)
        stats=self.run_portfolio(data.df,entry_exits,TpSlComb(tp=0.05,sl=0.03))

    def run_portfolio(self,df:pd.DataFrame,entry_exits: EntryExitResult,tp_sl: TpSlComb) -> pd.DataFrame: #TODO: Size и size_type исправить на percent 0.1
        direction=self.config.strategy.type.get_direction()
        params={

            "entries":entry_exits.long_entries,
            "exits":entry_exits.long_exits,
            "short_entries":entry_exits.short_entries,
            "short_exits":entry_exits.short_exits,
            "direction": direction,
            "upon_opposite_entry":'close',
            "tp_stop":tp_sl.tp,
            "sl_stop":tp_sl.sl,
            "size":100,
            "fees":0.001,
            "init_cash":10000,
            "size_type":'value',
            "freq":df.index.freq,
        }
        if direction=='both':
            params.pop('direction')
        elif direction=='longonly':
            params.pop('short_entries')
        else:
            params.pop('entries')
        stats=(vbt.Portfolio.from_signals(
            close=df['Close'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            **params
        )).stats(agg_func=None)
        #TODO: Убрать
        stats['Total Return [%]']=stats['Total Return [%]']*100

        return stats



    def get_result_from_backtest(self,data:BackTestData,params:Dict):
        df=data.df
        entry_exits=self._get_entries_and_exists(params,close=df['Close'].values,
                                                 open=df['Open'].values,
                                                 high=df['High'].values,
                                                 low=df['Low'].values,
                                                 volume=df['Volume'].values)

        if self.config.use_fast():
            entry_exits,tp_sl=self._get_tp_sl(entry_exits)
            result=self.run_portfolio(df,entry_exits,tp_sl)
        else:# self.config.strategy.size.use_fast:
            result=self._combination_via_tp_sl(df,entry_exits)

        backtest_result=BackTestResult(coin=data.coin,result=result)
        self.data_handler.save_result(backtest_result)


    def run_backtest_one_coin(self,data:BackTestData,total:int,idx_symbol:int):
        self._prepare_njit(data,self.params.single.to_dict())
        self._prepare_njit(data,self.params.single.to_dict())
        total_comb=self.params_comb.get_total_combinations()
        for idx,params in enumerate(self.params_comb.init_batch(self.config.processor.max_chunks,self.data_handler.get_combination_done(data.coin))):
            try:
                self.get_result_from_backtest(data,params)
                progress_sym=((idx*self.config.processor.max_chunks)/total_comb)
                self.progress_dict[self.pid]=(data.coin,progress_sym,idx_symbol,total)
                # logger.info(self.progress_dict[self.pid])
            except Exception as e:
                logger.exception(f'Error handled\n {e}')


    def run(self):
        total=len(self.symbols)
        try:
            for idx,symbol in enumerate(self.symbols):
                self.progress_dict[self.pid]=(symbol,0.0,idx,total)
                df=self.data_handler.get_or_empty_df(symbol)
                if not df.empty:
                    data=BackTestData(coin=symbol,df=df)
                    self.run_backtest_one_coin(data,total,idx)
                else:
                    logger.info(f'Empty dataframe, symbol = {symbol}')
        except Exception as e:
            logger.exception(f'Critical Error when backtest {e}')
        finally:
            logger.info(f'Finished PID {self.pid}')
            self.progress_dict[self.pid] = ("done", 1.0, total,total)







