from dataclasses import dataclass
from typing import Callable, Generic, TypeVar
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


INTERESTED_SAIL_SIZES = ('4.9', '5.0', '5.1', '5.2', '5.8', '5.9', '6.0', '6.1', '6.2')


def includes_point_7(string: str) -> bool:
    return 'point-7' in string.lower() or 'point7' in string.lower()


def sail_filter(sail: Sail) -> bool:
    if includes_point_7(sail.brand):
        return True

    state_ok = 'new' in sail.state.lower() or 'used' in sail.state.lower()
    size_ok = any(size in sail.size for size in INTERESTED_SAIL_SIZES)

    price = sail.metadata.price
    price_ok = True if isinstance(price, str) else (60 <= price <= 250)

    return state_ok and size_ok and price_ok


def mast_filter(mast: Mast) -> bool:
    length_ok = '460' in mast.length
    sdm_ok = 'sdm' in mast.rdm_or_sdm.lower()
    carbon_ok = any(carbon in mast.carbon for carbon in ('80', '85', '90', '95', '100'))

    point_7_ok = includes_point_7(mast.brand)

    return length_ok and sdm_ok and carbon_ok and point_7_ok


def full_set_filter(full_set: FullSet) -> bool:
    if includes_point_7(full_set.content_description):
        return True

    sail_ok = any(size in full_set.content_description for size in INTERESTED_SAIL_SIZES)

    return sail_ok


def full_rig_filter(full_rig: FullRig) -> bool:
    if includes_point_7(full_rig.sail.brand):
        return True

    sail_ok = any(size in full_rig.sail.size for size in INTERESTED_SAIL_SIZES)
    state_ok = 'new' in full_rig.sail.state.lower() or 'used' in full_rig.sail.state.lower()

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
