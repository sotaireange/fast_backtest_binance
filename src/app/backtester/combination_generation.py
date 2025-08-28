import itertools
from math import prod
from typing import Any, Dict, Generator, Iterator, List,Optional
from src.app.models import ParamConfig
import pandas as pd

import itertools
from typing import Any, Dict, Iterator, List


class BatchIterator:
    def __init__(
            self,
            params: Dict[str, List[Any]],
            batch_size: int,
            flag_forbidden: bool = False,
            flag_keys: List[str] = None,
            exclude_combos=None  # список tuple’ов для исключения
    ):
        self.params = params
        self.batch_size = batch_size
        self.flag_forbidden = flag_forbidden
        self.flag_keys = flag_keys or []
        self.exclude_combos = set(exclude_combos) if exclude_combos is not None else None

        self._all_combos = list(itertools.product(*(params[k] for k in params)))
        self._keys = list(params.keys())

        if self.flag_forbidden and self.flag_keys:
            self._all_combos = [
                combo for combo in self._all_combos
                if any(combo[self._keys.index(k)] for k in self.flag_keys)
            ]

        if self.exclude_combos:
            self._all_combos = [
                combo for combo in self._all_combos
                if combo not in self.exclude_combos
            ]

        self._pos = 0

    def __iter__(self) -> Iterator[Dict[str, List[Any]]]:
        return self

    def __next__(self) -> Dict[str, List[Any]]:
        if self._pos >= len(self._all_combos):
            raise StopIteration

        batch_combos = self._all_combos[self._pos:self._pos + self.batch_size]
        self._pos += self.batch_size

        result = {k: [] for k in self._keys}
        for combo in batch_combos:
            for k, v in zip(self._keys, combo):
                result[k].append(v)

        return result



class ParamCombinationsGenerator: #TODO: Сделать так , чтобы flag aroon/main был только один
    #TODO: Сделать комбинацию с ТП СЛ
    def __init__(self, config: ParamConfig):
        self.config = config

    def _expand(self, p) -> List[Any]:
        if hasattr(p, 'min') and hasattr(p, 'max') and hasattr(p, 'step'):
            return list(range(p.min, p.max + 1, p.step))
        if isinstance(p, bool):
            return [True, False] if p else [False]
        return p if isinstance(p, list) else [p]

    def _prepare_params(self) -> Dict[str, Any]:
        return {k: self._expand(v) for k, v in self.config.multi.to_dict().items()}

    def _flag_keys(self, params: Dict[str, Any]) -> List[str]:
        return [k for k in params if k.startswith('flag_')]

    def _is_valid(self, combo: Dict[str, Any], flag_keys: List[str]) -> bool:
        return not flag_keys or any(combo.get(k, False) for k in flag_keys)

    def get_total_combinations(self) -> int:
        params = self._prepare_params()
        flag_forbidden = getattr(self.config.settings, 'flag_forbidden', False)
        flag_keys = self._flag_keys(params) if flag_forbidden else []

        total = 0
        for combo in itertools.product(*(params[k] for k in params)):
            combo_dict = dict(zip(params, combo))
            if self._is_valid(combo_dict, flag_keys):
                total += 1
        return total

    def _max_batch_shape(self, params: Dict[str, Any], max_product: int) -> Dict[str, int]:
        list_keys = [k for k, v in params.items() if isinstance(v, list)]
        lengths = {k: len(params[k]) for k in list_keys}
        shape = {k: 1 for k in list_keys}

        for k in list_keys:
            shape[k] = min(lengths[k], max_product // prod(shape.values()) or 1)
        return shape

    def init_batch(self, batch_size: int,exclude_combos:Optional[pd.MultiIndex]) -> BatchIterator:
        params = self._prepare_params()
        flag_forbidden = getattr(self.config.settings, 'flag_forbidden', False)
        flag_keys = self._flag_keys(params) if flag_forbidden else []

        exclude_combos = list(map(tuple, exclude_combos)) if exclude_combos is not None and not exclude_combos.empty else []
        return BatchIterator(
            params,
            batch_size,
            flag_forbidden,
            flag_keys,
            exclude_combos
        )


    def generate_all_combinations(self) -> Generator[Dict[str, Any], None, None]:
        params = self._prepare_params()
        flag_forbidden = getattr(self.config.settings, 'flag_forbidden', False)
        flag_keys = self._flag_keys(params) if flag_forbidden else []

        for combo in itertools.product(*(params[k] for k in params)):
            combo_dict = dict(zip(params, combo))
            if self._is_valid(combo_dict, flag_keys):
                yield combo_dict
