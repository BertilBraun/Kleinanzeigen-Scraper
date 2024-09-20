from dataclasses import dataclass


OPENAI_API_KEY = 'sk-your-openai-api-key'  # Your OpenAI API key here
GEOAPIFY_API_KEY = 'your-geoapify-api-key'  # Your Geoapify API key here
MAILJET_API_KEY = 'your-mailjet-api-key'  # Your Mailjet API key here
MAILJET_SECRET_KEY = 'your-mailjet-secret-key'  # Your Mailjet secret key here
MAILJET_FROM_EMAIL = 'your-mailjet-email'  # The email address that you logged into Mailjet with
EMAILS_TO_NOTIFY = ['your-email']  # The email addresses to send notifications to

BASE_URL_KLEINANZEIGEN = 'https://www.kleinanzeigen.de'
BASE_URL_DAILYDOSE = 'https://www.dailydose.de'
WINDSURF_SEARCH_URLS = [
    BASE_URL_KLEINANZEIGEN + '/s-karlsruhe/anzeige:angebote/seite:{}/windsurfen/k0l9186r50',
    BASE_URL_KLEINANZEIGEN + '/s-sindelfingen/anzeige:angebote/seite:{}/windsurfen/k0l8991r30',
    BASE_URL_DAILYDOSE + '/kleinanzeigen/windsurfboards.htm?pg={}',
    BASE_URL_DAILYDOSE + '/kleinanzeigen/windsurfsegel.htm?pg={}',
]
# Format (PLZ, radius in km, name)
INTEREST_LOCATIONS = [
    (71034, 30, 'Böblingen'),
    (76133, 50, 'Karlsruhe'),
]
MAX_NUM_IMAGES = 3
DO_REQUERY_OLD_OFFERS = False


@dataclass
class InterestRequest:
    description: str
    max_price: int | None = None
    max_distance: int | None = None  # in km
    # data fields from the excel export that should include one of the terms in the list
    # a offer is filtered out if it does not match any of the terms in the list
    fields: dict[str, list[str]] = {}


def INTERESTS() -> dict[type, InterestRequest]:
    from src.types_to_search import Board, Sail, Mast, Boom  # noqa
    # types have to be imported here to avoid circular imports

    return {
        Sail: InterestRequest(
            '4.0 - 6.8 m², Freeride or Freemove only, unrepaired but used sails are fine',
            max_price=250,
            fields={'Sail Type': ['Freeride', 'Freemove']},
        ),
    }


LLM_MODEL_ID = 'gpt-4o-mini'

DB_FILE = 'db.json'
CURRENT_OFFERS_FILE = 'current_offers.json'
OFFER_IMAGE_DIR = 'offer_images'
EXCEL_EXPORT_FILE = 'export.xlsx'
