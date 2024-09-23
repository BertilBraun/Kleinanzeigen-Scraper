from dataclasses import dataclass
from typing import Callable, Generic, TypeVar
from src.types_to_search import ENTRY_TYPES, Board, Sail, Mast, Boom  # noqa

T = TypeVar('T', bound=ENTRY_TYPES)


@dataclass
class InterestRequest(Generic[T]):
    description: str | None = None
    max_price: int | None = None
    max_distance: int | None = None  # in km
    filter: Callable[[T], bool] | None = None


def sail_filter(sail: Sail) -> bool:
    if 'point-7' in sail.brand.lower() or 'point7' in sail.brand.lower():
        return True

    state_ok = 'new' in sail.state.lower() or 'used' in sail.state.lower()
    size_ok = any(size in sail.size for size in ('4.9', '5.0', '5.1', '5.2', '5.8', '5.9', '6.0', '6.1'))
    return state_ok and size_ok


def mast_filter(mast: Mast) -> bool:
    length_ok = '460' in mast.length
    sdm_ok = 'sdm' in mast.rdm_or_sdm.lower()
    carbon_ok = any(carbon in mast.carbon for carbon in ('75', '80', '85', '90', '95', '100'))

    return length_ok and sdm_ok and carbon_ok


INTERESTS: dict[type, InterestRequest] = {
    Sail: InterestRequest[Sail](
        max_price=250,
        max_distance=130,
        filter=sail_filter,
    ),
    Mast: InterestRequest[Mast](
        max_price=350,
        max_distance=130,
        filter=mast_filter,
    ),
}
