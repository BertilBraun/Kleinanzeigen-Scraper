from __future__ import annotations
import os
import json

import pandas as pd

from dataclasses import Field, dataclass, field, fields
from typing import Callable


from src.config import INTEREST_LOCATIONS, OFFER_IMAGE_DIR
from src.lat_long import distance, plz_to_lat_long
from src.util import log_all_exceptions, to_lower_snake_case, parse_numeric, to_readable_name, overrides


@dataclass
class ExcelExportType:
    number_format: str | None
    value: str | float | pd.Timestamp


@dataclass
class User:
    id: str
    name: str
    rating: str
    all_offers_link: str

    @staticmethod
    def from_json(json_data: dict) -> 'User':
        return User(
            id=json_data['id'],
            name=json_data['name'],
            rating=json_data['rating'],
            all_offers_link=json_data['all_offers_link'],
        )


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
    scraped_on: pd.Timestamp
    user: User

    @staticmethod
    def from_json(data: dict) -> Offer:
        user_data = data.pop('user')
        user = User.from_json(user_data)

        if 'scraped_on' not in data:
            scraped_on = pd.Timestamp.now()
        else:
            scraped_on = pd.to_datetime(data['scraped_on'], errors='ignore', dayfirst=True)

        return Offer(
            user=user,
            id=data['id'],
            title=data['title'],
            description=data['description'],
            price=data['price'],
            location=data['location'],
            date=data['date'],
            link=data['link'],
            sold=data['sold'],
            image_urls=data['image_urls'],
            scraped_on=scraped_on,
        )


class DatabaseFactory:
    @staticmethod
    def from_json(json_data: dict) -> list[Entry]:
        with log_all_exceptions('while parsing database entries'):
            return [DatabaseFactory.parse_entry(entry) for entry in json_data]

    @staticmethod
    def parse_entry(json_data: dict) -> Entry:
        metadata = Metadata.from_json(json_data.pop('metadata'))
        return DatabaseFactory._parse_entry(json_data, metadata)

    @staticmethod
    def parse_parial_entry(json_data: dict, offer: Offer, lat_long: tuple[float, float]) -> Entry:
        type = json_data.pop('type')
        metadata = Metadata(type=type, offer=offer, lat_long=lat_long)
        return DatabaseFactory._parse_entry(json_data, metadata)

    @staticmethod
    def _parse_entry(json_data: dict, metadata: Metadata) -> Entry:
        from src.types_to_search import ALL_TYPES

        for type_ in ALL_TYPES + [Uninteresting]:
            if do_types_match(metadata, type_):
                return type_.from_json(metadata=metadata, json_data=json_data)

        raise ValueError(f'Unknown type: {metadata.type}')


@dataclass
class Metadata:
    type: str
    offer: Offer
    lat_long: tuple[float, float]

    @staticmethod
    def from_json(json_data: dict) -> Metadata:
        offer = Offer.from_json(json_data['offer'])
        return Metadata(offer=offer, type=json_data['type'], lat_long=json_data['lat_long'])

    @property
    def distance_to_interest_locations(self) -> dict[str, float]:
        return {name: distance(self.lat_long, plz_to_lat_long(location)) for location, _, name in INTEREST_LOCATIONS}

    @property
    def closest_interest_location(self) -> tuple[str, float]:
        return min(
            self.distance_to_interest_locations.items(),
            key=lambda x: (x[1], x[0]),
        )

    def to_excel(self) -> dict[str, ExcelExportType]:
        min_distance, closest_place_name = self.closest_interest_location
        return {
            'Price': ExcelExportType(
                number_format='#0 €',
                value=parse_numeric(
                    self.offer.price.replace(',-', '')
                    .replace('.-', '')
                    .replace(',', '.')
                    .replace('€', '')
                    .replace('Euro', '')
                    .replace('VB', '')
                    .replace('VHB', '')
                    .strip()
                ),
            ),
            'VB': ExcelExportType(
                number_format=None, value='VB' if 'VB' in self.offer.price or 'VHB' in self.offer.price else ''
            ),
            'Location': ExcelExportType(number_format=None, value=self.offer.location),
            'Date': ExcelExportType(
                number_format='DD/MM/YYYY',
                value=pd.to_datetime(self.offer.date, errors='ignore', dayfirst=True),
            ),
            'Sold': ExcelExportType(number_format=None, value='Sold' if self.offer.sold else ''),
            'Link': ExcelExportType(number_format=None, value=self.offer.link),
            'Images': ExcelExportType(number_format=None, value=os.path.abspath(OFFER_IMAGE_DIR + '/' + self.offer.id)),
            'User name': ExcelExportType(number_format=None, value=self.offer.user.name),
            'All other offers': ExcelExportType(number_format=None, value=self.offer.user.all_offers_link),
            'Scraped on': ExcelExportType(number_format='DD/MM/YYYY HH:MM:SS', value=self.offer.scraped_on),
            'Min Distance (km)': ExcelExportType(
                number_format='#0', value=f'{min_distance:.2f} km to {closest_place_name}'
            ),
        }


@dataclass
class Entry:
    metadata: Metadata

    def to_excel(self, do_add_metadata: bool = True) -> dict[str, ExcelExportType]:
        data: dict[str, ExcelExportType] = {}
        for f in fields(self):
            if is_parameter(f):
                data[to_readable_name(f.name)] = ExcelExportType(
                    number_format=f.metadata['number_format'],
                    value=f.metadata['value_transformer'](getattr(self, f.name)),
                )
        if do_add_metadata:
            data.update(self.metadata.to_excel())
        return data

    @classmethod
    def generate_json_description(cls) -> str:
        # Automatically generate the description dictionary from the dataclass fields
        description_dict = {'type': to_lower_snake_case(cls.__name__)}

        for f in fields(cls):
            if is_parameter(f):
                description_dict[f.name] = f.metadata['description']

        return json.dumps(description_dict, indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, metadata: Metadata, json_data: dict) -> Entry:
        parameters = {f.name: json_data.get(f.name, '') for f in fields(cls) if is_parameter(f)}

        return cls(metadata=metadata, **parameters)


@dataclass
class Uninteresting(Entry):
    @overrides(Entry)
    def to_excel(self) -> dict[str, ExcelExportType]:
        return {
            'Title': ExcelExportType(number_format=None, value=self.metadata.offer.title),
            **self.metadata.to_excel(),
        }

    @staticmethod
    def from_offer(offer: Offer, lat_long: tuple[float, float]) -> Uninteresting:
        return Uninteresting(metadata=Metadata(type='uninteresting', offer=offer, lat_long=lat_long))


def parameter(
    description: str,
    number_format: str | None = None,
    value_transformer: Callable[[str], str | float | pd.Timestamp] = lambda x: x,
):
    return field(
        metadata={
            'description': description,
            'number_format': number_format,
            'value_transformer': value_transformer,
            'is_parameter': True,
        },
        init=True,
        kw_only=True,
    )


def is_parameter(f: Field) -> bool:
    return f.metadata.get('is_parameter', False)


def list_entries_of_type(entries: list[Entry], type: type[Entry]) -> list[Entry]:
    return [entry for entry in entries if do_types_match(entry.metadata, type)]


def do_types_match(metadata: Metadata, type: type[Entry]) -> bool:
    return metadata.type == to_lower_snake_case(type.__name__)
