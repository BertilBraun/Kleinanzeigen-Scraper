import json
import base64


from src.config import MAX_NUM_IMAGES, OFFER_IMAGE_DIR
from src.types_to_search import ALL_TYPES
from src.types import DatabaseFactory, Entry, Offer, Uninteresting, to_readable_name
from src.util import async_gpt_request


def base64_encode_image(image: bytes) -> str:
    return base64.b64encode(image).decode('utf-8')


def get_example_image() -> str:
    # load example_prompt_image.jpeg and convert to base64
    with open('data/example_prompt_image.jpeg', 'rb') as file:
        return base64_encode_image(file.read())


def load_and_convert_images_to_base64(offer_id: str, max_num_images: int) -> list[str]:
    base64_images: list[str] = []

    for i in range(max_num_images):
        try:
            with open(f'{OFFER_IMAGE_DIR}/{offer_id}/{i}.jpg', 'rb') as file:
                base64_images.append(base64_encode_image(file.read()))
        except FileNotFoundError:
            # Assuming, that this offer did contain less than max_num_images images
            break
        except Exception as e:
            print(f'Failed to read image file: {e}')
            break

    return base64_images


def get_type_descriptions() -> str:
    all_names = [to_readable_name(t.__name__) for t in ALL_TYPES]
    all_type_names = ', '.join(all_names[:-1]) + ' and ' + all_names[-1]

    all_type_descriptions = ''

    for name, type_ in zip(all_names, ALL_TYPES):
        all_type_descriptions += f'{name}:\n```json\n{type_.generate_json_description()}\n```\n\n\n'

    return f"""The types of equipment include {all_type_names}. 

If the information is not available or cannot be determined from the input, use "".

You should output the information in the following JSON format based on the type of equipment:

{all_type_descriptions}"""


def get_extraction_prompt(offer: Offer):
    base64_example_image = get_example_image()
    base64_images = load_and_convert_images_to_base64(offer.id, MAX_NUM_IMAGES)

    return [
        {
            'role': 'system',
            'content': f"""You are a helpful assistant that extracts information from offers related to Windsurf equipment and converts it into a specific JSON format. {get_type_descriptions()}

If the type of equipment cannot be determined or is not relevant to usable windsurf equipment, use:
```json
{{
  "type": "N/A"
}}
```
This will be for items like child equipment, courses, toys, display figures, etc. which are not relevant to windsurfing.

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
    ]


async def extract_offer_details(offer: Offer, lat_long: tuple[float, float]) -> Entry:
    success, res = await async_gpt_request(get_extraction_prompt(offer), response_format={'type': 'json_object'})

    if not success:
        print(f'Failed to get the response for offer: {offer.title} ({offer.link}) {offer.image_urls[:MAX_NUM_IMAGES]}')
        return Uninteresting.from_offer(offer, lat_long)

    try:
        json_data = json.loads(res)
        if json_data['type'].lower() == 'n/a':
            return Uninteresting.from_offer(offer, lat_long)

        return DatabaseFactory.parse_parial_entry(json_data, offer, lat_long)
    except Exception:
        print('Failed to parse the JSON response:', res)
        return Uninteresting.from_offer(offer, lat_long)
