from dataclasses import dataclass
from src.types import DatabaseFactory, Entry, ExcelExportType, Metadata, parameter
from src.util import parse_numeric, indent, overrides


@dataclass
class Sail(Entry):
    size: str = parameter('Size of the Sail in m²', '#,#0.0', parse_numeric)
    brand: str = parameter('Name of the Brand and Model')
    mast_length: str = parameter(
        'Length of the required Mast in cm. Most of the time visible on a picture underneath "Luff" on the Sail.',
        '#0',
        parse_numeric,
    )
    boom_size: str = parameter(
        'Size of the required Boom in cm. Most of the time visible on a picture underneath "Boom" on the Sail.',
        '#0',
        parse_numeric,
    )
    sail_type: str = parameter('Wave, Freestyle, Freemove, Freeride, Freerace, Slalom, Racing')
    year: str = parameter('Release Year')
    state: str = parameter('new, used, repaired, demaged, defective')


@dataclass
class Board(Entry):
    size: str = parameter('Dimensions of the Board')
    brand: str = parameter('Name of the Brand and Model')
    board_type: str = parameter('Freeride, Wave, Freestyle, Slalom, ...')
    volume: str = parameter(
        'Volume in Liters',
        '#0',
        lambda x: parse_numeric(x.lower().replace('liters', '').replace('liter', '').replace('l', '').strip()),
    )
    year: str = parameter('Release Year')


@dataclass
class Mast(Entry):
    brand: str = parameter('Name of the Brand and Model')
    length: str = parameter('Length of the Mast in cm', '#0', parse_numeric)
    carbon: str = parameter('Carbon Percentage', '#.#0.0', parse_numeric)
    rdm_or_sdm: str = parameter('Either RDM or SDM')


@dataclass
class Boom(Entry):
    brand: str = parameter('Name of the Brand and Model')
    size: str = parameter('Minimum and Maximum Size of the Boom in cm (e.g., 140-190)')
    year: str = parameter('Release Year')


@dataclass
class FullSet(Entry):
    content_description: str = parameter(
        'Short description of what the set includes (e.g., Sail, Mast, Boom, Board, etc.)'
    )


@dataclass
class FullRig(Entry):
    sail: Sail = parameter('To be generated below')
    mast: Mast = parameter('To be generated below')
    boom: Boom = parameter('To be generated below')

    @overrides(Entry)
    def to_excel(self, do_add_metadata: bool = True) -> dict[str, ExcelExportType]:
        sail = {f'Sail {key}': value for key, value in self.sail.to_excel().items()}
        mast = {f'Mast {key}': value for key, value in self.mast.to_excel().items()}
        boom = {f'Boom {key}': value for key, value in self.boom.to_excel().items()}
        data = {**sail, **mast, **boom}
        if do_add_metadata:
            data.update(self.metadata.to_excel())
        return data

    @classmethod
    @overrides(Entry)
    def generate_json_description(cls) -> str:
        return f"""{{
  "type": "full_rig",
  "sail": {indent(Sail.generate_json_description())[2:]},
  "mast": {indent(Mast.generate_json_description())[2:]},
  "boom": {indent(Boom.generate_json_description())[2:]}
}}"""

    @classmethod
    @overrides(Entry)
    def from_json(cls, metadata: Metadata, json_data: dict) -> Entry:
        json_data['sail']['type'] = 'sail'
        sail = DatabaseFactory.parse_parial_entry(json_data['sail'], metadata.offer, metadata.lat_long)
        json_data['mast']['type'] = 'mast'
        mast = DatabaseFactory.parse_parial_entry(json_data['mast'], metadata.offer, metadata.lat_long)
        json_data['boom']['type'] = 'boom'
        boom = DatabaseFactory.parse_parial_entry(json_data['boom'], metadata.offer, metadata.lat_long)
        return FullRig(metadata=metadata, sail=sail, mast=mast, boom=boom)  # type: ignore


@dataclass
class Accessory(Entry):
    accessory_type: str = parameter(
        'Mastfoot, Mast extension, Harness Lines, Fins, Harness, Impact Vest, etc. Should be the Type of the Accessory, followed by a short description. E.g., "Harness Lines: 24-30 inch adjustable"'
    )


ENTRY_TYPES = Sail | Board | Mast | Boom | FullSet | FullRig | Accessory
ALL_TYPES: list[type[ENTRY_TYPES]] = [Sail, Board, Mast, Boom, FullSet, FullRig, Accessory]
