from src.lat_long import plz_to_lat_long

OPENAI_API_KEY = 'sk-your-openai-api-key'  # Your OpenAI API key here

BASE_URL = 'https://www.kleinanzeigen.de'
WINDSURF_SEARCH_URLS = [
    BASE_URL + '/s-karlsruhe/seite:{}/windsurfen/k0l9186r50',
    BASE_URL + '/s-sindelfingen/seite:{}/windsurfen/k0l8991r30',
]
INTEREST_LOCATIONS = [
    (plz_to_lat_long(71034), 30),  # Böblingen 30km
    (plz_to_lat_long(76133), 50),  # Karlsruhe 50km
]
MAX_OFFERS_PER_PAGE = 25
OFFER_PAGE_BATCH_SIZE = 10
MAX_NUM_IMAGES = 3

LLM_MODEL_ID = 'gpt-4o-mini'

DB_FILE = 'db.json'
CURRENT_OFFERS_FILE = 'current_offers.json'
FILTERED_OUT_OFFERS_FILE = 'filtered_out_offers.json'
