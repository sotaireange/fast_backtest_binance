import asyncio

from src.common.loggers import get_logger
from src.app.models.config_schema import MainConfig

from src.app.data.downloader import BinanceDataDownloader

log=get_logger('downloader',True)

async def start_download(config:MainConfig):
    async with BinanceDataDownloader(config) as bdd:
        await bdd.download_multiple_symbols()
