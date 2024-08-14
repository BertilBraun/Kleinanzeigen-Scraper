OPENAI_API_KEY = 'sk-your-openai-api-key'  # Your OpenAI API key here
GEOAPIFY_API_KEY = 'your-geoapify-api-key'  # Your Geoapify API key here

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

LLM_MODEL_ID = 'gpt-4o-mini'

DB_FILE = 'db.json'
CURRENT_OFFERS_FILE = 'current_offers.json'
OFFER_IMAGE_DIR = 'offer_images'
