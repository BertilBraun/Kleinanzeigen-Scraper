import asyncio
from tqdm import tqdm
from math import ceil
from typing import Any, Coroutine, List, Callable, TypeVar

from src.util.contextmanager import log_all_exceptions

T = TypeVar('T')  # Input type
R = TypeVar('R')  # Output type


async def _after_batch_noop(_: List[R]) -> bool:
    return True


# Define the generic batched async executor
async def run_in_batches(
    items: List[T],
    batch_size: int,
    async_func: Callable[[T], Coroutine[Any, Any, R]],
    desc: str | None = 'Processing',
    do_ignore_errors: bool = True,
    after_batch: Callable[[List[R]], Coroutine[Any, Any, bool]] = _after_batch_noop,
) -> List[R]:
    # Run the async function for each item in the list in batches
    # and return the results in the correct order
    # After each batch, the after_batch function is called with the results of the batch, the function should return True to continue processing the next batch

    # Initialize a list to store results in the correct order
    results: list[R] = [None] * len(items)  # type: ignore

    if not desc:
        iterable = range(0, len(items), batch_size)
    else:
        iterable = tqdm(
            range(0, len(items), batch_size),
            desc=desc,
            unit='batch',
            total=ceil(len(items) / batch_size),
        )

    for batch_start in iterable:
        batch_end = min(batch_start + batch_size, len(items))
        batch = items[batch_start:batch_end]
        item_futures = [async_func(item) for item in batch]

        for i, future in enumerate(asyncio.as_completed(item_futures)):
            # Wait for the result and store it in the corresponding position
            if do_ignore_errors:
                with log_all_exceptions('while processing batch'):
                    results[batch_start + i] = await future
            else:
                results[batch_start + i] = await future

        if not await after_batch(results[batch_start:batch_end]):
            break

    return results
