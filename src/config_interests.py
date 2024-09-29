from dataclasses import dataclass
from typing import Callable, Generic, Iterable, TypeVar
from src.types_to_search import ENTRY_TYPES, Board, Sail, Mast, Boom, FullRig, FullSet  # noqa


TITLE_NO_GO_KEYWORDS = ('gesucht', 'suche', 'wing', 'kite', 'north face', 'neo', 'kind')

T = TypeVar('T', bound=ENTRY_TYPES)


@dataclass
class InterestRequest(Generic[T]):
    description: str | None = None  # description to query GPT with, for GPT to decide if it's interesting or not
    min_price: int | None = None
    max_price: int | None = None
    max_distance: int | None = None  # in km
    filter: Callable[[T], bool] | None = None


INTERESTED_SAIL_SIZES = ('4.9', '5.0', '5.1', '5.2', '5.8', '5.9', '6.0', '6.1', '6.2', '8.3', '8.4', '8.5', '8.6')
STATE_NO_GO_KEYWORDS = ('repaired', 'demaged', 'defective')
POINT_7 = ('point-7', 'point7')


def contains(string: str, words: Iterable[str]) -> bool:
    return any(word in string.lower() for word in words)


def not_contains(string: str, words: Iterable[str]) -> bool:
    return all(word not in string.lower() for word in words)


def sail_filter(sail: Sail) -> bool:
    if contains(sail.brand, POINT_7):
        return True

    size_ok = contains(sail.size, INTERESTED_SAIL_SIZES)
    state_ok = not_contains(sail.state, STATE_NO_GO_KEYWORDS)

    price = sail.metadata.price
    price_ok = True if isinstance(price, str) else (60 <= price <= 250)
    slalom_ok = not_contains(sail.sail_type, ('slalom',))

    return state_ok and size_ok and price_ok and slalom_ok


def mast_filter(mast: Mast) -> bool:
    length_ok = '460' in mast.length
    sdm_ok = 'sdm' in mast.rdm_or_sdm.lower()
    carbon_ok = contains(mast.carbon, ('80', '85', '90', '95', '100'))
    point_7_ok = contains(mast.brand, POINT_7)

    return length_ok and sdm_ok and carbon_ok and point_7_ok


def full_set_filter(full_set: FullSet) -> bool:
    if contains(full_set.content_description, POINT_7):
        return True

    sail_ok = contains(full_set.content_description, INTERESTED_SAIL_SIZES)

    return sail_ok


def full_rig_filter(full_rig: FullRig) -> bool:
    if contains(full_rig.sail.brand, POINT_7):
        return True

    sail_ok = contains(full_rig.sail.size, INTERESTED_SAIL_SIZES)
    state_ok = not_contains(full_rig.sail.state, STATE_NO_GO_KEYWORDS)

    return sail_ok and state_ok


INTERESTS: dict[type, InterestRequest] = {
    Sail: InterestRequest[Sail](
        max_distance=130,
        filter=sail_filter,
    ),
    Mast: InterestRequest[Mast](
        max_price=350,
        max_distance=130,
        filter=mast_filter,
    ),
    FullSet: InterestRequest[FullSet](
        max_distance=130,
        filter=full_set_filter,
    ),
    FullRig: InterestRequest[FullRig](
        max_distance=130,
        filter=full_rig_filter,
    ),
}
