import inspect
import yaml

from src.app.strategies.registry import strategy_registry
import os

from typing import Callable


def generate_yaml_template(func:Callable,func_name:str=''):
    sig = inspect.signature(func)
    config = {"settings":{'flag_forbidden': False},
             "multi":{},
             "single":{}}
    for name, param in sig.parameters.items():
        if param.annotation is int:
            config['multi'][name] = {
                "min": 10,
                "max": 50,
                "step": 1
            }
            config['single'][name]=10
        elif param.annotation is bool:
            config['multi'][name] = False
            config['single'][name]=False

    if func_name=='':
        func_name=((func.__name__.split('_'))[1])

    with open(f'config/{func_name}_strategy_config.yaml', "w") as f:
        yaml.dump(config, f, sort_keys=False, allow_unicode=True)
    return yaml.dump(config)



def generate_all_template():
    for name,func in strategy_registry.items():
        if not os.path.exists(f'config/{name}_strategy_config.yaml'):
            generate_yaml_template(func,name)


if __name__=='__main__':
    generate_all_template()