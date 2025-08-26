import pandas as pd

from src.common.loggers import get_logger

from src.app.data.csv_handler import DataHandler
from src.app.models import MainConfig
from src.app.data.types import COLUMNS_RESULT


logger=get_logger('analyser',False)

class TradingAnalyser:
    def __init__(self, config: MainConfig):
        self.config=config
        self.data_handler=DataHandler(config)
        self.df:pd.DataFrame = self.data_handler.get_all_result()


    def get_aggregate_analysis(self):
        param_levels = self.df.index.names[:-1]

        agg =(self.df.groupby(level=param_levels)
              ).mean(numeric_only=True)

        top100 = agg.sort_values("Total Return [%]", ascending=False).head(100)
        self.data_handler.save_analysis(top100,'top100_total')



    def get_aggregate_by_symbol(self):
        param_levels = self.df.index.names[:-1]
        symbol_level = "symbol"

        best_per_symbol = (
            self.df.groupby(level=symbol_level, group_keys=False)
            .apply(lambda x: x.sort_values("Total Return [%]", ascending=False).head(1))
        )

        best_combos = best_per_symbol.index.droplevel("symbol").unique()
        filtered = self.df.loc[self.df.index.droplevel("symbol").isin(best_combos)]
        agg = filtered.groupby(level=param_levels).mean(numeric_only=True)
        self.data_handler.save_analysis(agg,'by_symbol')


    def save_grouped_by_symbol(self):
        grouped=self.df.groupby(level="symbol", group_keys=False)
        best_per_symbol = (
            grouped
            .apply(lambda x: x.sort_values("Total Return [%]", ascending=False).head(100))
        )
        best_per_symbol_by_winrate=(
            grouped
            .apply(lambda x: x.sort_values("Win Rate [%]", ascending=False).head(100))
    )
        for symbol,df_sym in best_per_symbol.groupby(level='symbol'):
            self.data_handler.save_analysis(df_sym,str(symbol),True)

        for symbol,df_sym in best_per_symbol_by_winrate.groupby(level='symbol'):
            self.data_handler.save_analysis(df_sym,f'{symbol}_winrate',True)



    def start_analysis(self):
        try:
            self.save_grouped_by_symbol()
            self.get_aggregate_by_symbol()
            self.get_aggregate_analysis()
        except Exception as e:
            logger.error(f'Error while analysis,\n {e}')
