from typing import Union,Dict,List,Optional
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp

from multiprocessing.managers import DictProxy

from src.app.data.downloader import get_symbols
from src.app.utils.helpers import chunkify

from src.app.backtester.engine import MultiParamPortfolioBacktest
from src.app.models import MainConfig
from src.common.loggers import get_logger

from src.app.utils.config_loader import get_main_config
from src.app.data.downloader import get_symbols
from src.app.utils.helpers import chunkify

log=get_logger('engine')

def run_portfolio(config_dict:Dict,pid:int,chunk:List[str],progress_dict:Optional[DictProxy]):
    config=MainConfig(**config_dict)
    bt=MultiParamPortfolioBacktest(config,pid,chunk,progress_dict)
    bt.run()

def run_backtest(config: MainConfig, chunks: List[List[str]] ,progress_dict: Optional[DictProxy]=None):
    config_dict = config.to_dict()
    processes = []
    for pid, chunk in enumerate(chunks):
        p = mp.Process(target=run_portfolio, args=(config_dict,pid, chunk, progress_dict))
        p.daemon = False
        processes.append(p)
        p.start()
    for p in processes:
        p.join()


if __name__ == '__main__':
    mp.freeze_support()
    config=get_main_config()
    symbols = get_symbols(config)
    chunks = chunkify(symbols, config.processor.max_processors)
    run_backtest(config,chunks=chunks)