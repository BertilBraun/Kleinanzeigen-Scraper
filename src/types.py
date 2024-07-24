from __future__ import annotations
from dataclasses import dataclass

import pandas as pd

from src.util import log_all_exceptions


@dataclass
class User:
    id: str
    name: str
    rating: str
    all_offers_link: str

    @staticmethod
    def from_json(json_data: dict) -> 'User':
        return User(**json_data)


@dataclass
class Offer:
    id: str
    title: str
    description: str
    price: str
    location: str
    date: str
    link: str
    sold: bool
    image_urls: list[str]
    user: User

    @staticmethod
    def from_json(json_data: dict) -> 'Offer':
        user_data = json_data.pop('user')
        user = User.from_json(user_data)
        return Offer(user=user, **json_data)


class DatabaseFactory:
    @staticmethod
    def from_json(json_data: dict) -> list[Entry]:
        with log_all_exceptions('while parsing database entries'):
            return [DatabaseFactory.parse_entry(entry) for entry in json_data]

    @staticmethod
    def parse_entry(json_data: dict) -> Entry:
        metadata = DatabaseFactory.Metadata.from_json(json_data.pop('metadata'))
        return DatabaseFactory._parse_entry(json_data, metadata)

    @staticmethod
    def parse_parial_entry(json_data: dict, offer: Offer) -> Entry:
        type = json_data.pop('type')
        metadata = DatabaseFactory.Metadata(type=type, offer=offer)
        return DatabaseFactory._parse_entry(json_data, metadata)

    @staticmethod
    def _parse_entry(json_data: dict, metadata: DatabaseFactory.Metadata) -> Entry:
        if metadata.type == 'sail':
            return DatabaseFactory.Sail(metadata=metadata, **json_data)
        elif metadata.type == 'board':
            return DatabaseFactory.Board(metadata=metadata, **json_data)
        elif metadata.type == 'mast':
            return DatabaseFactory.Mast(metadata=metadata, **json_data)
        elif metadata.type == 'boom':
            return DatabaseFactory.Boom(metadata=metadata, **json_data)
        elif metadata.type == 'full_set':
            return DatabaseFactory.FullSet(metadata=metadata, **json_data)
        elif metadata.type == 'full_rig':
            sail = DatabaseFactory.Sail(metadata=metadata, **json_data.pop('sail').pop('type'))
            mast = DatabaseFactory.Mast(metadata=metadata, **json_data.pop('mast').pop('type'))
            boom = DatabaseFactory.Boom(metadata=metadata, **json_data.pop('boom').pop('type'))
            return DatabaseFactory.FullRig(metadata=metadata, sail=sail, mast=mast, boom=boom)
        elif metadata.type == 'accessory':
            return DatabaseFactory.Accessory(metadata=metadata, **json_data)
        elif metadata.type == 'uninteresting':
            return DatabaseFactory.Uninteresting(metadata=metadata)
        else:
            raise ValueError(f'Unknown type: {metadata.type}')

    @dataclass
    class Metadata:
        type: str
        offer: Offer

        @staticmethod
        def from_json(json_data: dict) -> DatabaseFactory.Metadata:
            offer_data = json_data.pop('offer')
            offer = Offer.from_json(offer_data)
            return DatabaseFactory.Metadata(offer=offer, **json_data)

        def to_excel(self) -> dict[str, ExcelExportType]:
            return {
                'Price': ExcelExportType(
                    number_format='#0 €',
                    value=parse_numeric(self.offer.price.replace('€', '').replace('VB', '').strip()),
                ),
                'VB': ExcelExportType(number_format=None, value='VB' if 'VB' in self.offer.price else ''),
                'Location': ExcelExportType(number_format=None, value=self.offer.location),
                'Date': ExcelExportType(
                    number_format='DD/MM/YYYY',
                    value=pd.to_datetime(self.offer.date, errors='ignore', dayfirst=True),
                ),
                'Sold': ExcelExportType(number_format=None, value='Sold' if self.offer.sold else ''),
                'Link': ExcelExportType(number_format=None, value=self.offer.link),
                'User name': ExcelExportType(number_format=None, value=self.offer.user.name),
                'All other offers': ExcelExportType(number_format=None, value=self.offer.user.all_offers_link),
            }

    @dataclass
    class Sail:
        metadata: DatabaseFactory.Metadata
        size: str
        brand: str
        mast_length: str
        boom_size: str
        year: str
        state: str

        def to_excel(self) -> dict[str, ExcelExportType]:
            return {
                'Size': ExcelExportType(number_format='#,#0.0', value=parse_numeric(self.size)),
                'Mast length': ExcelExportType(number_format='#0', value=parse_numeric(self.mast_length)),
                'Boom size': ExcelExportType(number_format='#0', value=parse_numeric(self.boom_size)),
                'Brand': ExcelExportType(number_format=None, value=self.brand),
                'Year': ExcelExportType(number_format=None, value=self.year),
                'State': ExcelExportType(number_format=None, value=self.state),
                **self.metadata.to_excel(),
            }

    @dataclass
    class Board:
        metadata: DatabaseFactory.Metadata
        size: str
        brand: str
        board_type: str
        volume: str
        year: str

        def to_excel(self) -> dict[str, ExcelExportType]:
            return {
                'Size': ExcelExportType(number_format=None, value=self.size),
                'Brand': ExcelExportType(number_format=None, value=self.brand),
                'Board type': ExcelExportType(number_format=None, value=self.board_type),
                'Volume': ExcelExportType(number_format='#0', value=parse_numeric(self.volume)),
                'Year': ExcelExportType(number_format=None, value=self.year),
                **self.metadata.to_excel(),
            }

    @dataclass
    class Mast:
        metadata: DatabaseFactory.Metadata
        brand: str
        length: str
        carbon: str
        rdm_or_sdm: str

        def to_excel(self) -> dict[str, ExcelExportType]:
            return {
                'Brand': ExcelExportType(number_format=None, value=self.brand),
                'Length': ExcelExportType(number_format='#0', value=parse_numeric(self.length)),
                'Carbon': ExcelExportType(number_format='#.#0.0', value=parse_numeric(self.carbon)),
                'RDM or SDM': ExcelExportType(number_format=None, value=self.rdm_or_sdm),
                **self.metadata.to_excel(),
            }

    @dataclass
    class Boom:
        metadata: DatabaseFactory.Metadata
        brand: str
        size: str
        year: str

        def to_excel(self) -> dict[str, ExcelExportType]:
            return {
                'Brand': ExcelExportType(number_format=None, value=self.brand),
                'Size': ExcelExportType(number_format=None, value=self.size),
                'Year': ExcelExportType(number_format=None, value=self.year),
                **self.metadata.to_excel(),
            }

    @dataclass
    class FullSet:
        metadata: DatabaseFactory.Metadata
        content_description: str

        def to_excel(self) -> dict[str, ExcelExportType]:
            return {
                'Content description': ExcelExportType(number_format=None, value=self.content_description),
                **self.metadata.to_excel(),
            }

    @dataclass
    class FullRig:
        metadata: DatabaseFactory.Metadata
        sail: DatabaseFactory.Sail
        mast: DatabaseFactory.Mast
        boom: DatabaseFactory.Boom

        def to_excel(self) -> dict[str, ExcelExportType]:
            sail = {f'Sail {key}': value for key, value in self.sail.to_excel().items()}
            mast = {f'Mast {key}': value for key, value in self.mast.to_excel().items()}
            boom = {f'Boom {key}': value for key, value in self.boom.to_excel().items()}
            return {**sail, **mast, **boom, **self.metadata.to_excel()}

    @dataclass
    class Accessory:
        metadata: DatabaseFactory.Metadata
        accessory_type: str

        def to_excel(self) -> dict[str, ExcelExportType]:
            return {
                'Accessory type': ExcelExportType(number_format=None, value=self.accessory_type),
                **self.metadata.to_excel(),
            }

    @dataclass
    class Uninteresting:
        metadata: DatabaseFactory.Metadata

        def to_excel(self) -> dict[str, ExcelExportType]:
            return {
                'Title': ExcelExportType(number_format=None, value=self.metadata.offer.title),
                **self.metadata.to_excel(),
            }

        @staticmethod
        def from_offer(offer: Offer) -> DatabaseFactory.Uninteresting:
            return DatabaseFactory.Uninteresting(metadata=DatabaseFactory.Metadata(type='uninteresting', offer=offer))


Entry = (
    DatabaseFactory.Sail
    | DatabaseFactory.Board
    | DatabaseFactory.Mast
    | DatabaseFactory.Boom
    | DatabaseFactory.FullSet
    | DatabaseFactory.FullRig
    | DatabaseFactory.Accessory
    | DatabaseFactory.Uninteresting
)


def parse_numeric(value: str) -> float | str:
    try:
        return float(value)
    except ValueError:
        return value


@dataclass
class ExcelExportType:
    number_format: str | None
    value: str | float | pd.Timestamp
