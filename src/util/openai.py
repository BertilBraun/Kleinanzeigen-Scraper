from typing import Optional, TypeVar
from openai import AsyncOpenAI
from pydantic import BaseModel

from src.config import LLM_MODEL_ID, OPENAI_API_KEY, OPENAI_BASE_URL
from src.util.contextmanager import cache_to_folder


T = TypeVar('T', bound=BaseModel)


@cache_to_folder('data/gpt_request_cache')
async def async_gpt_request(
    prompt: list,
    model: type[T],
    temperature: float = 0.0,
) -> Optional[T]:
    # Async request to the LLM_MODEL_ID model with the given prompt and temperature
    # Returns a tuple with a boolean indicating if the request was successful and the response content
    client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

    try:
        response = await client.beta.chat.completions.parse(
            model=LLM_MODEL_ID,
            messages=prompt,
            temperature=temperature,
            response_format=model,
        )
    except Exception:
        return None

    return response.choices[0].message.parsed
