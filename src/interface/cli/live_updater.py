import multiprocessing as mp
import time
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from src.common.loggers import get_logger, console
from src.app.models import MainConfig
from src.scripts.run_backtest import run_portfolio
from src.app.data.downloader import get_symbols
from src.app.utils.helpers import chunkify

log = get_logger('app', False)

def run_backtest_with_liveupdater(config: MainConfig):
    symbols = get_symbols(config)
    chunks = chunkify(symbols, config.processor.max_processors)

    with mp.Manager() as manager:
        progress_dict = manager.dict({pid: ('idle', 0.0, 0, len(chunk)) for pid, chunk in enumerate(chunks)})
        processes = []
        config_dict = config.to_dict()

        for pid, chunk in enumerate(chunks):
            p = mp.Process(target=run_portfolio, args=(config_dict,pid, chunk, progress_dict))
            processes.append(p)
            p.start()

        with Progress(
                TextColumn("[bold blue]{task.fields[pid]}[/bold blue]"),
                TextColumn("{task.fields[symbol]}"),
                BarColumn(),
                TextColumn("{task.percentage:>3.0f}%"),
                TextColumn("{task.fields[completed_syms]}/{task.fields[total_syms]}"),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=console,
        ) as progress:

            tasks = {}
            for pid, chunk in enumerate(chunks):
                tasks[pid] = progress.add_task(
                    "", total=1.0, pid=f"PID {pid}", symbol="Waiting...",
                    completed_syms=0, total_syms=len(chunk)
                )

            # Обновление прогресса
            while any(p.is_alive() for p in processes):
                for pid, task_id in tasks.items():
                    symbol, prog, num_sym, total = progress_dict[pid]
                    progress.update(
                        task_id,
                        completed=prog,
                        symbol=symbol if symbol not in ("idle", "done") else "Waiting" if symbol=="idle" else "Done",
                        completed_syms=num_sym,
                        total_syms=total
                    )
                time.sleep(0.1)

        for p in processes:
            p.join()

        console.print("\n[bold green]🎉 All task done[/bold green]")
