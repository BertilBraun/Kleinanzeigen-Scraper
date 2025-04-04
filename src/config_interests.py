from dataclasses import dataclass
from typing import Callable, Generic, Iterable, TypeVar
from src.types_to_search import ENTRY_TYPES, Board, Sail, Mast, Boom, FullRig, FullSet  # noqa


TITLE_NO_GO_KEYWORDS = ('gesucht', 'suche', 'wing', 'kite', 'north face', 'neo', 'kind', ' sup ')


BASE_URL_KLEINANZEIGEN = 'https://www.kleinanzeigen.de'
BASE_URL_DAILYDOSE = 'https://www.dailydose.de/kleinanzeigen'
WINDSURF_SEARCH_URLS = [
    BASE_URL_KLEINANZEIGEN + '/s-seite:{}/windsurf/k0',
    BASE_URL_DAILYDOSE + '/windsurfboards.htm?pg={}',
    BASE_URL_DAILYDOSE + '/windsurfsegel.htm?pg={}',
    BASE_URL_DAILYDOSE + '/windsurfmasten.htm?pg={}',
    BASE_URL_DAILYDOSE + '/windsurfgabeln.htm?pg={}',
] + [
    BASE_URL_KLEINANZEIGEN + '/s-freizeit-nachbarschaft/seite:{}/' + brand + '/k0c185'
    for brand in [
        'fanatic',
        # 'jp-australia',
        # 'starboard',
        # 'tabou',
        # 'rrd',
        # 'naish',
        # 'simmer',
        'north',
        'goya',
        'gunsails',
        'gun-sails',
        # 'point-7',
        'severne',
        'duotone warp',
        'duotone s pace',
        'duotone s type',
        'duotone e pace',
        'duotone e type',
        'north sails',
        'neilpryde',
        'patrik',
        # 'gaastra',
        # keywords
        # 'freeride',
        'freerace',
        'slalom',
        # 'blast',
        # 'magic ride',
        # 'gecko',
        # 'firemove',
    ]
]

# Format (PLZ, radius in km, name)
INTEREST_LOCATIONS = [
    (71034, 100, 'Böblingen'),
    (76133, 100, 'Karlsruhe'),
    # (77855, 30, 'Achern'),
    # (77656, 30, 'Offenburg'),
    # (77955, 30, 'Ettenheim'),
    # (79100, 30, 'Freiburg'),
    (79848, 30, 'Bonndorf'),
    (50667, 60, 'Köln'),
    (89073, 100, 'Ulm'),
    (80331, 100, 'München'),
    # (71034, 2000, 'Böblingen'),  # Simply all of Germany
]

T = TypeVar('T', bound=ENTRY_TYPES)


@dataclass
class InterestRequest(Generic[T]):
    description: str | None = None  # description to query GPT with, for GPT to decide if it's interesting or not
    min_price: int | None = None
    max_price: int | None = None
    min_year: int | None = None  # year of manufacture (2012, 2013, ...)
    max_distance: int | None = None  # in km
    filter: Callable[[T], bool] | None = None


INTERESTED_SAIL_SIZES = [
    '4.9',
    '5.0',
    '5.1',
    '5.2',
    '5.3',
    '5.4',
    '5.5',
    '5.6',
    '5.7',
    '5.8',
    '5.9',
] + [str(i / 10) for i in range(60, 100)]
INTERESTED_SAILS = [
    'warp',
    's type',
    'e type',
    'e pace',
    's pace',
    'gs-r',
    'gs r',
    'vector',
    'mach',
    'v8',
    'moto',
    'gt-3',
    'patrik',
    'turbo',
    'speedster',
    'ncx',
]
RACE_SAIL_TYPES = [
    'freerace',
    'slalom',
    'race',
    'speed',
]
STATE_NO_GO_KEYWORDS = []  # ('repaired', 'demaged', 'defective')
POINT_7 = ('point-7', 'point7')


def contains(string: str, words: Iterable[str]) -> bool:
    return any(word.lower() in string.lower() for word in words)


def not_contains(string: str, words: Iterable[str]) -> bool:
    return all(word.lower() not in string.lower() for word in words)


def sail_filter(sail: Sail) -> bool:
    if contains(sail.brand, POINT_7):
        return False

    size_ok = contains(sail.size, INTERESTED_SAIL_SIZES)
    state_ok = not_contains(sail.state, STATE_NO_GO_KEYWORDS)
    keyword_ok = (
        contains(sail.metadata.offer.title, INTERESTED_SAIL_SIZES + INTERESTED_SAILS)
        or contains(sail.metadata.offer.description, INTERESTED_SAIL_SIZES + INTERESTED_SAILS)
        or contains(sail.sail_type, RACE_SAIL_TYPES)
    )

    return state_ok and size_ok and keyword_ok


def mast_filter(mast: Mast) -> bool:
    length_ok = '460' in mast.length
    sdm_ok = 'sdm' in mast.rdm_or_sdm.lower()
    carbon_ok = contains(mast.carbon, ('80', '85', '90', '95', '100'))
    point_7_ok = contains(mast.brand, POINT_7)

    return length_ok and sdm_ok and carbon_ok and point_7_ok


def full_set_filter(full_set: FullSet) -> bool:
    if contains(full_set.content_description, POINT_7):
        return False

    sail_ok = (
        contains(full_set.content_description, INTERESTED_SAIL_SIZES + INTERESTED_SAILS)
        or contains(full_set.metadata.offer.title, INTERESTED_SAIL_SIZES + INTERESTED_SAILS)
        or contains(full_set.metadata.offer.description, INTERESTED_SAIL_SIZES + INTERESTED_SAILS)
        or contains(full_set.content_description, RACE_SAIL_TYPES)
    )

    return sail_ok


def full_rig_filter(full_rig: FullRig) -> bool:
    if contains(full_rig.sail.brand, POINT_7):
        return False

    sail_ok = (
        contains(full_rig.sail.size, INTERESTED_SAIL_SIZES)
        or contains(full_rig.metadata.offer.title, INTERESTED_SAIL_SIZES + INTERESTED_SAILS)
        or contains(full_rig.metadata.offer.description, INTERESTED_SAIL_SIZES + INTERESTED_SAILS)
        or contains(full_rig.sail.sail_type, RACE_SAIL_TYPES)
    )
    state_ok = not_contains(full_rig.sail.state, STATE_NO_GO_KEYWORDS)

    return sail_ok and state_ok


INTERESTS: dict[type, InterestRequest] = {
    Sail: InterestRequest[Sail](
        max_distance=230,
        min_price=60,
        max_price=500,
        min_year=2012,
        filter=sail_filter,
    ),
    FullSet: InterestRequest[FullSet](
        max_distance=230,
        min_price=60,
        filter=full_set_filter,
    ),
    FullRig: InterestRequest[FullRig](
        max_distance=230,
        min_price=60,
        filter=full_rig_filter,
    ),
}
