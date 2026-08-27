"""
Thin wrapper around the google-genai SDK.
Two entry points:
  - generate_text(...)   -> plain string, for cover-letter prose etc.
  - generate_json(...)   -> parsed dict/list, using a response schema
"""
import json
from google import genai
from google.genai import types

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config

import logging

logger = logging.getLogger(__name__)

_clients = [genai.Client(api_key=k) for k in config.API_KEYS]
_current_key_idx = 0

def _execute_with_retry(func):
    global _current_key_idx
    max_retries = len(_clients)
    for i in range(max_retries):
        client = _clients[_current_key_idx]
        try:
            return func(client)
        except Exception as e:
            # Check if it's a rate limit error (429)
            is_rate_limit = False
            if hasattr(e, 'code') and e.code == 429:
                is_rate_limit = True
            elif '429' in str(e):
                is_rate_limit = True
            
            if is_rate_limit:
                _current_key_idx = (_current_key_idx + 1) % len(_clients)
                logger.warning(f"Rate limited. Rotating to API key index {_current_key_idx} ({i+1}/{max_retries} attempts)")
                continue
            else:
                raise
    
    raise Exception("All configured API keys are currently rate limited.")

def generate_text(prompt: str, system_instruction: str = "", model: str = None,
                   temperature: float = 0.4) -> str:
    model = model or config.MODEL_REASONING
    
    def _call(client):
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction or None,
                temperature=temperature,
            ),
        )
        return response.text.strip()
        
    return _execute_with_retry(_call)


def generate_json(prompt: str, response_schema: dict, system_instruction: str = "",
                   model: str = None, temperature: float = 0.2):
    """
    response_schema: a JSON-schema-like dict (OpenAPI subset) describing the
    expected shape. Gemini will constrain output to match it.
    """
    model = model or config.MODEL_REASONING
    
    def _call(client):
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction or None,
                temperature=temperature,
                response_mime_type="application/json",
                response_schema=response_schema,
            ),
        )
        return json.loads(response.text)
        
    return _execute_with_retry(_call)
