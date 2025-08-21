import asyncio
import multiprocessing


from rich.prompt import Prompt
from rich.table import Table


from src.app.utils.config_loader import get_main_config
from src.interface.cli.live_updater import run_backtest_with_liveupdater
from src.scripts.run_download import run_download
from src.scripts.generate_configs import generate_all_template

from src.common.loggers import console,get_logger


log = get_logger('app',True)



def show_menu():
    """Выводит меню команд"""
    table = Table(title="Commands", show_lines=True)
    table.add_column("Command", style="cyan", justify="center")
    table.add_column("Description", style="green")
    table.add_row("run", "Run backtest all params.")
    table.add_row("download", "Download data")
    table.add_row("analysis", "Run analysis")
    table.add_row("exit", "Exit from app.")
    console.print(table)

async def run_cli():
    show_menu()
    generate_all_template()
    while True:
        command = Prompt.ask("[bold yellow]Enter command[/]", default="run").strip().lower()
        config=get_main_config()
        if command in ['run','download']:
            text = '~5 min.' if config.strategy.symbols.use_all else '<1 min.'
            log.info(f"Downloading data. Please wait. Estimated time: {text}")
            await run_download(config)
            log.info("Data download completed ✅")
        if command == "run":
            log.info("Starting backtest for all parameters...")
            run_backtest_with_liveupdater(config)
            log.info("Backtest completed ✅")

        elif command == "analysis":
            log.info("Starting analysis...")
            log.info("Analysis completed ✅")


        elif command in ("exit", "quit"):
            log.info("Exiting the program...")
            break
        elif command=='test':
            log.info("Test function")
        else:
            console.print("[bold red]Unknown command[/] ❌")
            show_menu()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    asyncio.run(run_cli())