import os
import json
import random
import time
from contextlib import contextmanager

from typing import Any, Callable, Coroutine, Generator

from src.util.json import custom_asdict, dump_json, load_json


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


def cache_to_folder(folder_name: str) -> Callable[..., Callable[..., Coroutine[Any, Any, Any]]]:
    # Wrapps a function that (optionally) returns a coroutine and caches the result to a file
    # The parameters are thereby used as the cache key, so the function should be deterministic
    def load_cache(folder_name: str) -> dict[str, Any]:
        assert os.path.isdir(folder_name), f'"{folder_name}" is not a folder'

        cache = {}
        for file_name in os.listdir(folder_name):
            if file_name.endswith('.json'):
                try:
                    cache.update(load_json(f'{folder_name}/{file_name}'))
                except Exception:
                    pass

        if random.random() < 0.01:  # 1% chance to clean up the cache
            dump_json(cache, f'{folder_name}/cache.json')
            for file_name in os.listdir(folder_name):
                if file_name.endswith('.json') and file_name != 'cache.json':
                    with log_all_exceptions(f'Failed to remove file: {file_name}'):
                        os.remove(f'{folder_name}/{file_name}')

        return cache

    def decorator(func) -> Callable[..., Coroutine[Any, Any, Any]]:
        async def wrapper(*args, **kwargs):
            os.makedirs(folder_name, exist_ok=True)
            cache = load_cache(folder_name)
            key = json.dumps(custom_asdict((args, kwargs)))
            if key in cache:
                return cache[key]
            del cache

            result = await func(*args, **kwargs)

            new_file_name = f'{folder_name}/{time.time()}.json'
            dump_json({key: custom_asdict(result)}, new_file_name)
            return result

        return wrapper

    return decorator
