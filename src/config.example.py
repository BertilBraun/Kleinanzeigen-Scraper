OPENAI_API_KEY = 'sk-your-openai-api-key'  # Your OpenAI API key here

BASE_URL = 'https://www.kleinanzeigen.de'
WINDSURF_SEARCH_URL = BASE_URL + '/s-karlsruhe/seite:{}/windsurfen/k0l9186r50'
MAX_OFFERS_PER_PAGE = 25
OFFER_PAGE_BATCH_SIZE = 10

LLM_MODEL_ID = 'gpt-4o-mini'

DB_FILE = 'db.json'
CURRENT_OFFERS_FILE = 'current_offers.json'
FILTERED_OUT_OFFERS_FILE = 'filtered_out_offers.json'
