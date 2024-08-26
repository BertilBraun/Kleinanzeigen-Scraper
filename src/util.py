import os
import json
import time
from enum import Enum
from typing import Any, Callable, Generator, Generic, Protocol, Type, TypeVar, overload
from contextlib import contextmanager
from dataclasses import is_dataclass

import pandas as pd


def write_to_file(file_name: str, content: str) -> None:
    dir_name = os.path.dirname(file_name)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(file_name, 'w') as f:
        f.write(content)


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


@contextmanager
def json_dumper(file_name: str) -> Generator[Callable[[Any], None], None, None]:
    # with json_dumper('data.json') as dumper:
    #    for i in range(3):
    #        dumper({'a': i})
    # This will write the following content to data.json:
    # [ {"a": 0}, {"a": 1}, {"a": 2} ]
    dir_name = os.path.dirname(file_name)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    with open(file_name, 'w') as f:
        f.write('[')
        first = True

        def write(obj: Any) -> None:
            nonlocal first
            if not first:
                f.write(',')
            f.write(json.dumps(custom_asdict(obj), indent=4))
            f.flush()
            first = False

        try:
            yield write
        finally:
            f.write(']')


@contextmanager
def log_all_exceptions(message: str = ''):
    try:
        yield
    except KeyboardInterrupt:
        # if e is keyboard interrupt, exit the program
        raise
    except Exception as e:
        print(f'Error occurred "{message}": {e}')

        import traceback

        traceback.print_exc()


@contextmanager
def timeblock(message: str):
    """
    with timeblock('Sleeping') as timer:
        time.sleep(2)
        print(f'Slept for {timer.elapsed_time} seconds')
        time.sleep(1)

    # Output:
    # Starting Sleeping
    # Slept for 2.001 seconds
    # Timing Sleeping took: 3.002 seconds
    """
    start_time = time.time()  # Record the start time

    class Timer:
        # Nested class to allow access to elapsed time within the block
        @property
        def elapsed_time(self):
            # Calculate elapsed time whenever it's requested
            return time.time() - start_time

    timer = Timer()

    print(f'Starting {message}')
    try:
        yield timer  # Allow the block to access the timer
    finally:
        print(f'Timing {message} took: {timer.elapsed_time:.3f} seconds')


def cache_to_file(file_name: str):
    # Wrapps a function that (optionally) returns a coroutine and caches the result to a file
    # The parameters are thereby used as the cache key, so the function should be deterministic

    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = {}
            if os.path.exists(file_name):
                with open(file_name, 'r') as f:
                    cache = json.load(f)
            key = json.dumps(custom_asdict((args, kwargs)))
            if key in cache:
                return cache[key]
            result = await func(*args, **kwargs)
            cache[key] = custom_asdict(result)
            with open(file_name, 'w') as f:
                json.dump(cache, f, indent=4)
            return result

        return wrapper

    return decorator
