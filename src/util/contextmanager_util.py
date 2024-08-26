import os
import json
import time
from contextlib import contextmanager

from typing import Any, Callable, Generator

from src.util.json_util import custom_asdict


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
