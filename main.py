import asyncio
import multiprocessing


from src.common.loggers import redirect_external_loggers_to_file

from src.interface.cli.cli import run_cli



if __name__ == '__main__':
    redirect_external_loggers_to_file()
    multiprocessing.freeze_support()
    asyncio.run(run_cli())