import os
import json
from enum import Enum
from typing import Any, Generic, Protocol, Type, TypeVar, overload
from dataclasses import is_dataclass

import pandas as pd

from src.util import write_to_file


def custom_asdict(obj):
    if is_dataclass(obj):
        result = {}
        for field_name, field_type in obj.__dataclass_fields__.items():
            value = getattr(obj, field_name)
            result[field_name] = custom_asdict(value)
        return result
    elif isinstance(obj, pd.Timestamp):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, list) or isinstance(obj, tuple):
        return tuple(custom_asdict(item) for item in obj)
    elif isinstance(obj, dict):
        return {key: custom_asdict(value) for key, value in obj.items()}
    elif callable(obj):
        return obj.__qualname__  # Save the function's qualname if it's a callable
    else:
        return obj


T = TypeVar('T')


class FromJsonProtocol(Protocol, Generic[T]):  # type: ignore
    @classmethod
    def from_json(cls: Any, data: dict) -> T:
        ...


@overload
def load_json(file_name: str) -> Any:
    ...


@overload
def load_json(file_name: str, obj_type: Type[FromJsonProtocol[T]]) -> list[T]:
    ...


def load_json(file_name: str, obj_type: Type[FromJsonProtocol[T]] | None = None) -> Any | list[T]:
    if not os.path.exists(file_name):
        print(f'File not found: {file_name}')
        exit(1)

    # Datei lesen und JSON laden
    with open(file_name, 'r') as f:
        file_content = f.read()
        try:
            json_data = json.loads(file_content)
        except json.JSONDecodeError:
            json_data = json.loads(file_content + ']')

    if obj_type is None:
        return json_data

    # Überprüfen, ob json_array eine Liste ist
    if not isinstance(json_data, list):
        raise ValueError('Das JSON-Objekt muss ein Array sein.')

    # Liste der Objekte erstellen
    obj_list: list[T] = []
    for entry in json_data:
        # Erstellen einer Instanz des obj_type und Initialisieren mit den JSON-Daten
        obj = obj_type.from_json(entry)
        obj_list.append(obj)

    return obj_list


def dump_json(obj: Any, file_name: str) -> None:
    if os.path.exists(file_name):
        write_to_file(file_name + '.bak', open(file_name).read())
    write_to_file(file_name, json.dumps(custom_asdict(obj), indent=4))
