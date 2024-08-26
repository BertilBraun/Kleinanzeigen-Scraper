import asyncio
import json
import base64

from openai import AsyncOpenAI

from src.requests import get_bytes
from src.config import MAX_NUM_IMAGES, OPENAI_API_KEY, LLM_MODEL_ID
from src.types import DatabaseFactory, Entry, Offer


def base64_encode_image(image: bytes) -> str:
    return base64.b64encode(image).decode('utf-8')


def get_example_image() -> str:
    # load example_prompt_image.jpeg and convert to base64
    with open('data/example_prompt_image.jpeg', 'rb') as file:
        return base64_encode_image(file.read())


async def download_and_convert_images(image_urls: list[str]) -> list[str]:
    image_bytes = await asyncio.gather(*[get_bytes(url) for url in image_urls])
    return [base64_encode_image(image) for image in image_bytes]


async def extract_offer_details(offer: Offer, lat_long: tuple[float, float]) -> Entry:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    base64_example_image = get_example_image()
    base64_images = await download_and_convert_images(offer.image_urls[:MAX_NUM_IMAGES])

    try:
        response = await client.chat.completions.create(
            model=LLM_MODEL_ID,
            messages=[
                {
                    'role': 'system',
                    'content': """You are a helpful assistant that extracts information from eBay Kleinanzeigen related to Windsurf equipment and converts it into a specific JSON format. The types of equipment include sails, boards, masts, booms, full sets, full rigs, and accessories. 

If the information is not available or cannot be determined from the input, use "".

You should output the information in the following JSON format based on the type of equipment:

Sail:
```json
{
  "type": "sail",
  "size": "Size of the Sail in m²",
  "brand": "Name of the Brand and Model",
  "mast_length": "Length of the required Mast in cm",
  "boom_size": "Size of the required Boom in cm",
  "year": "Release Year",
  "state": "new, used, repaired, demaged, defective"
}
```

Board:
```json
{
  "type": "board",
  "size": "Dimensions of the Board",
  "brand": "Name of the Brand and Model",
  "board_type": "Freeride, Wave, Freestyle, Slalom, Formula, ...",
  "volume": "Volume in Liters",
  "year": "Release Year"
}
```

Mast:
```json
{
  "type": "mast",
  "brand": "Name of the Brand and Model",
  "length": "Length of the Mast in cm",
  "carbon": "Carbon Percentage",
  "rdm_or_sdm": "Either RDM or SDM"
}
```

Boom:
```json
{
  "type": "boom",
  "brand": "Name of the Brand and Model",
  "size": "Minimum and Maximum Size of the Boom in cm",
  "year": "Release Year"
}
```

Full Set:
```json
{
  "type": "full_set",
  "content_description": "Short description of what the set includes (e.g., Sail, Mast, Boom, Board, etc.)"
}
```

Full Rig:
```json
{
  "type": "full_rig",
  "sail": {
    "type": "sail",
    "size": "Size of the Sail in m²",
    "brand": "Name of the Brand and Model",
    "mast_length": "Length of the required Mast in cm",
    "boom_size": "Size of the required Boom in cm",
    "year": "Release Year",
    "state": "new, used, repaired, demaged, defective"
  },
  "mast": {
    "type": "mast",
    "brand": "Name of the Brand and Model",
    "length": "Length of the Mast in cm",
    "carbon": "Carbon Percentage",
    "rdm_or_sdm": "Either RDM or SDM"
  },
  "boom": {
    "type": "boom",
    "brand": "Name of the Brand and Model",
    "size": "Minimum and Maximum Size of the Boom in cm",
    "year": "Release Year"
  }
}
```

Accessory:
```json
{
  "type": "accessory",
  "accessory_type": "Mastfoot, Mast extension, Harness Lines, Fins, etc.",
}
```

If the type of equipment cannot be determined or is not relevant to usable windsurf equipment, use:
```json
{
  "type": "N/A"
}
```
This will be for items like child equipment, courses, toys, etc. which are not relevant to windsurfing.

""",
                },
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': """As an example, let's extract the details of the following offer:
---

Convert the following offer into the appropriate JSON format:

Title: North Spectro 6.5 Surfsegel Windsurfen
Description: Segel mit wenigen Gebrauchsspuren. 2 Band-Camber als Profilgeber. Ein kleiner getapteter Cut im Unterliek. gerne auch mit Carbonmast + 20€""",
                        },
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:image/png;base64,{base64_example_image}',
                                'detail': 'low',  # The image is already downsampled to 512x512
                            },
                        },
                    ],
                },
                {
                    'role': 'assistant',
                    'content': """{
  "type": "sail",
  "size": "6.5",
  "brand": "North Spectro",
  "mast_length": "4.92",
  "boom_size": "1.95",
  "year": "N/A",
  "state": "repaired"
}""",
                },
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': f"""Convert the following offer into the appropriate JSON format:

Title: {offer.title}
Description: {offer.description}""",
                        },
                        *[
                            {
                                'type': 'image_url',
                                'image_url': {'url': f'data:image/png;base64,{image}', 'detail': 'low'},
                            }
                            for image in base64_images
                        ],
                    ],
                },
            ],
            temperature=0.0,
            response_format={'type': 'json_object'},
        )
    except Exception as e:
        print(
            f'Failed to get the response: {e} for offer: {offer.title} ({offer.link}) {offer.image_urls[:MAX_NUM_IMAGES]}'
        )
        return DatabaseFactory.Uninteresting.from_offer(offer, lat_long)

    try:
        response_json = response.choices[0].message.content
        if not response_json:
            print('Failed to extract the details of the offer:', offer.title)
            return DatabaseFactory.Uninteresting.from_offer(offer, lat_long)

        json_data = json.loads(response_json)
        if json_data['type'] == 'N/A':
            return DatabaseFactory.Uninteresting.from_offer(offer, lat_long)

        return DatabaseFactory.parse_parial_entry(json_data, offer, lat_long)
    except:  # noqa
        print('Failed to parse the JSON response:', response_json)
        return DatabaseFactory.Uninteresting.from_offer(offer, lat_long)
