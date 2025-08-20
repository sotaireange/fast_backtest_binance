from typing import Callable, Dict, Any,List
import inspect
import numpy as np
from vectorbt import IndicatorFactory
from vectorbt.indicators.factory import IndicatorBase



strategy_registry: Dict[str, Any] = {}
_cached_indicators = {}


def get_list_names(func:Callable,is_params:bool=False):
    sig = inspect.signature(func)
    result=[]
    for name,params in sig.parameters.items():
        if params.annotation is np.ndarray and not is_params:
            result.append(name)
        elif (params.annotation is not np.ndarray) and is_params:
            result.append(name)
    return result


def register_indicator(name: str):
    def decorator(obj: Any):
        strategy_registry[name] = obj
        return obj
    return decorator

def get_indicator(name: str) -> Any:
    if name not in strategy_registry:
        raise ValueError(f"Indicator '{name}' not found.")
    return strategy_registry[name]

def list_indicator() -> list[str]:
    return list(strategy_registry.keys())


def get_strategy(name:str) -> type[IndicatorBase]:
    func=get_indicator(name)
    list_input_names=get_list_names(func,False)
    list_params_names=get_list_names(func,True)

    indicator=IndicatorFactory(
        class_name=name,
        input_names=list_input_names,
        param_names=list_params_names,
        output_names=['buy', 'sell']
    ).from_apply_func(func)

    _cached_indicators[name] = indicator

    return indicator