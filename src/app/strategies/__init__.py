import os
import importlib
from .registry import get_strategy,get_indicator


def auto_import_strategies():
    current_dir = os.path.dirname(__file__)
    module_prefix = __name__  # 'strategies'

    for filename in os.listdir(current_dir):
        if filename.endswith(".py") and filename not in ("__init__.py", "registry.py"):
            module_name = f"{module_prefix}.{filename[:-3]}"
            importlib.import_module(module_name)

auto_import_strategies()
