"""
OpenRouter client — drop-in replacement for Anthropic API.
Uses OpenAI-compatible endpoint at openrouter.ai.
"""
import os
from openai import OpenAI

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
MODEL = 'openai/gpt-3.5-turbo'

import sys
print(f'[OpenRouter] key set={bool(OPENROUTER_API_KEY)} model={MODEL}', file=sys.stderr, flush=True)

def get_client() -> OpenAI:
    return OpenAI(
        base_url='https://openrouter.ai/api/v1',
        api_key=OPENROUTER_API_KEY,
    )

def call_model(system_prompt: str, user_content: str, max_tokens: int = 300) -> str:
    """Call OpenRouter model. Returns text response or empty string on error."""
    try:
        client = get_client()
        resp = client.chat.completions.create(
            model=MODEL,
            max_tokens=max_tokens,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user',   'content': user_content},
            ]
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        import sys
        print(f'[OpenRouter] error: {e}', file=sys.stderr, flush=True)
        return ''
