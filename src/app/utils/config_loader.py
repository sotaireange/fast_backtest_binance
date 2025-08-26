import yaml
from src.app.models.config_schema import MainConfig
from src.app.models.strategy_config_scheme import ParamConfig
from src.app.strategies import get_indicator
from src.scripts.generate_configs import generate_yaml_template


def get_main_config() -> MainConfig:
    with open("config/config.yaml", "r") as f:
        config_data = yaml.safe_load(f)
    main_config = MainConfig(**config_data)
    return main_config


def get_param_config(name:str) -> ParamConfig:
    strategy_param_file = f"config/{name}_strategy_config.yaml"

    try:
        with open(strategy_param_file, "r") as f:
            strategy_params_data = yaml.safe_load(f)
    except FileNotFoundError:
        func=get_indicator(name)
        strategy_param_data=generate_yaml_template(func,name)
    strategy_config = ParamConfig(**strategy_params_data)

    return strategy_config


