import pandas as pd
from pydantic import BaseModel, Field
from typing import List, Dict,Tuple
from datetime import datetime
import yaml
import numpy as np

#TODO: Make Config Better. Do it better settings like on/of TP/SL, choise Stock/Crypto. All settings to take from config.
# Как это сделать. Попробовать расширить настройки до стокового, чтобы можно было настройками расширить функциональность до того, что я делаю.
# Улучшить Бектест. Сделать несколько вариантов сохранения параметров. И т.д.

class TypeConfig(BaseModel):
    long: bool
    short: bool

    def get_direction(self):
        if self.long and self.short:
            return 'both'
        elif self.short:
            return 'shortonly'
        else:
            return 'longonly'

class TpSlConfig(BaseModel):
    use_fix: bool
    fix: float
    min: float
    max: float
    step: float
    use_custom: bool

class SizeConfig(BaseModel):
    use_fast: bool # use for vectorized
    use_only_tp_sl: bool # False for use exit with tp/sl
    trailing: bool # True - use trailing
    tp_pct: TpSlConfig
    sl_pct: TpSlConfig
    amount: float

    def get_combinations(self) -> pd.MultiIndex:
        '''
        Get combination Tp And Sl
        :return:
        '''
        tp_stops = np.arange(self.tp_pct.min, self.tp_pct.max+self.tp_pct.step, self.tp_pct.step) if not self.tp_pct.use_fix else self.tp_pct.fix
        sl_stops = np.arange(self.sl_pct.min, self.sl_pct.max+self.sl_pct.step, self.sl_pct.step) if not self.sl_pct.use_fix else self.sl_pct.fix
        tp_grid, sl_grid = np.meshgrid(tp_stops, sl_stops)
        tp_params = tp_grid.flatten()
        sl_params = sl_grid.flatten()
        param_index = pd.MultiIndex.from_arrays([sl_params, tp_params], names=['sl_stop', 'tp_stop'])

        return param_index


class TimeConfig(BaseModel):
    start_date: datetime
    end_date: datetime
    timeframe: str

class ModeConfig(BaseModel):
    mode: str


class SymbolsConfig(BaseModel):
    use_all: bool
    symbols: List[str]

class StrategyConfig(BaseModel):
    name: str
    use_combination: bool
    type: TypeConfig
    size: SizeConfig
    time: TimeConfig
    symbols: SymbolsConfig

class ProcessorConfig(BaseModel):
    max_processors: int
    max_chunks: int

class StockConfig(BaseModel):
    top: str #500,1000,5000
    use_list: bool
    tickers: List[str]


class TickersConfig(BaseModel):
    use_crypto: bool
    stock: StockConfig
    crypto: SymbolsConfig


class MainConfig(BaseModel): #TODO: Поменять Strategy - на отдельных конфиг Symbols
    strategy: StrategyConfig
    #tickers: TickersConfig
    processor: ProcessorConfig

    def __repr__(self):
        # Конвертируем в dict и выводим как YAML с отступами
        data = self.dict()
        return yaml.dump(data, sort_keys=False, default_flow_style=False)

    def to_dict(self) -> Dict:
        return self.dict()
    def use_fast(self):
        size_cfg = self.strategy.size
        return (
                not (size_cfg.tp_pct.use_fix and size_cfg.sl_pct.use_fix)
                or size_cfg.use_fast
                or size_cfg.use_vectorbt
        )

    def get_date(self) -> Tuple[datetime,datetime]:
        return self.strategy.time.start_date,self.strategy.time.end_date