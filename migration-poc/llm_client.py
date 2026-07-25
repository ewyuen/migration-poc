"""LLM client using OpenRouter API"""
import requests
import json
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, MODEL


def call_llm(prompt: str, system: str = "", max_tokens: int = 2000, temperature: float = 0.7) -> str:
    """
    Call DeepSeek via OpenRouter API

    Args:
        prompt: User message/prompt
        system: System prompt for context
        max_tokens: Max response length
        temperature: Sampling temperature (lower = more deterministic)

    Returns:
        LLM response text
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/ewyuen/migration-poc",
        "X-Title": "Agentic C# Migration POC",
    }

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    try:
        response = requests.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error calling LLM: {e}")
        raise


def call_llm_json(prompt: str, system: str = "", max_tokens: int = 2000) -> dict:
    """Call LLM and parse JSON response"""
    response = call_llm(prompt, system, max_tokens)

    # Try to extract JSON from response
    import re
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Fallback: try parsing entire response
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {"raw_response": response}
