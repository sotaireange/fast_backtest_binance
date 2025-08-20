from pydantic import BaseModel, RootModel
from typing import Union, Dict

class ParamRange(BaseModel):
    min: int
    max: int
    step: int


ParamValue = Union[ParamRange, float, int,bool]

class ParamModeConfig(RootModel[Dict[str, ParamValue]]):

    def get(self,name:str):
        return self.root.get(name)

    def to_dict(self):
        return dict(self.root.items())

    def __repr__(self) -> str:
        lines = []
        for name, value in self.root.items():
            if isinstance(value, ParamRange):
                line = f"{name} : {value.min}-{value.max}-{value.step}"
            else:
                line = f"{name} : {value}"
            lines.append(line)
        return "\n".join(lines)

class ParamSettings(BaseModel):
    flag_forbidden: bool

class ParamConfig(BaseModel):
    multi: ParamModeConfig
    single: ParamModeConfig
    settings: ParamSettings

    def __repr__(self) -> str:
        parts = []
        for mode in ['multi', 'single']:
            val = getattr(self, mode)
            part = f"{mode}:\n{repr(val)}"
            parts.append(part)
        return "\n\n".join(parts)