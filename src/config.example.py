from src.lat_long import plz_to_lat_long

OPENAI_API_KEY = 'sk-your-openai-api-key'  # Your OpenAI API key here

BASE_URL_KLEINANZEIGEN = 'https://www.kleinanzeigen.de'
BASE_URL_DAILYDOSE = 'https://www.dailydose.de'
WINDSURF_SEARCH_URLS = [
    BASE_URL_KLEINANZEIGEN + '/s-karlsruhe/seite:{}/windsurfen/k0l9186r50',
    BASE_URL_KLEINANZEIGEN + '/s-sindelfingen/seite:{}/windsurfen/k0l8991r30',
    BASE_URL_DAILYDOSE + '/kleinanzeigen/windsurfboards.htm?pg={}',
    BASE_URL_DAILYDOSE + '/kleinanzeigen/windsurfsegel.htm?pg={}',
]
INTEREST_LOCATIONS = [
    (plz_to_lat_long(71034), 30),  # Böblingen 30km
    (plz_to_lat_long(76133), 50),  # Karlsruhe 50km
]
MAX_NUM_IMAGES = 3
DO_REQUERY_OLD_OFFERS = False

LLM_MODEL_ID = 'gpt-4o-mini'

DB_FILE = 'db.json'
CURRENT_OFFERS_FILE = 'current_offers.json'
