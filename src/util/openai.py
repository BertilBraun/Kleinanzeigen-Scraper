from openai import AsyncOpenAI, OpenAI
from openai.types.chat.completion_create_params import ResponseFormat

from src.config import LLM_MODEL_ID, OPENAI_API_KEY, OPENAI_BASE_URL
from src.util.contextmanager import cache_to_folder


@cache_to_folder('data/gpt_request_cache')
def sync_gpt_request(
    prompt: list,
    temperature: float = 0.0,
    response_format: ResponseFormat = {'type': 'text'},
) -> tuple[bool, str]:
    # Sync request to the LLM_MODEL_ID model with the given prompt and temperature
    # Returns a tuple with a boolean indicating if the request was successful and the response content
    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL_ID,
            messages=prompt,
            temperature=temperature,
            response_format=response_format,
        )
    except Exception:
        return False, ''

    return response.choices[0].message.content is not None, response.choices[0].message.content or ''


@cache_to_folder('data/gpt_request_cache')
async def async_gpt_request(
    prompt: list,
    temperature: float = 0.0,
    response_format: ResponseFormat = {'type': 'text'},
) -> tuple[bool, str]:
    # Async request to the LLM_MODEL_ID model with the given prompt and temperature
    # Returns a tuple with a boolean indicating if the request was successful and the response content
    client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

    try:
        response = await client.beta.chat.completions.parse(
            model=LLM_MODEL_ID,
            messages=prompt,
            temperature=temperature,
            response_format=response_format,
        )
    except Exception:
        return False, ''

    return response.choices[0].message.content is not None, response.choices[0].message.content or ''
