from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import requests

DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash-lite",
    "claude": "claude-haiku-4-5",
    "openai": "gpt-4o-mini",
}

RetrySleep = Callable[[float], None]


def summarize(
    text: str,
    *,
    provider: str,
    model: str | None,
    api_key: str,
    system: str,
    max_output_tokens: int,
    temperature: float,
    gemini_thinking_budget: int = 0,
    max_retries: int = 5,
    timeout: int = 180,
    base_url: str | None = None,
) -> str:
    if not api_key:
        raise RuntimeError(f"Missing API key for provider '{provider}'.")
    provider = provider.lower()
    selected_model = model or DEFAULT_MODELS.get(provider)
    if not selected_model:
        raise RuntimeError(f"Unsupported provider: {provider}")
    if provider == "gemini":
        return _summarize_gemini(
            text,
            model=selected_model,
            api_key=api_key,
            system=system,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            gemini_thinking_budget=gemini_thinking_budget,
            max_retries=max_retries,
            timeout=timeout,
        )
    if provider == "claude":
        return _summarize_claude(
            text,
            model=selected_model,
            api_key=api_key,
            system=system,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )
    if provider == "openai":
        return _summarize_openai(
            text,
            model=selected_model,
            api_key=api_key,
            system=system,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            base_url=base_url,
        )
    raise RuntimeError(f"Unsupported provider: {provider}")


def _summarize_gemini(
    text: str,
    *,
    model: str,
    api_key: str,
    system: str,
    max_output_tokens: int,
    temperature: float,
    gemini_thinking_budget: int,
    max_retries: int,
    timeout: int,
) -> str:
    try:
        from google import genai
        from google.genai import types
    except Exception:
        return _summarize_gemini_rest(
            text,
            model=model,
            api_key=api_key,
            system=system,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            gemini_thinking_budget=gemini_thinking_budget,
            max_retries=max_retries,
            timeout=timeout,
        )
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=text,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            thinking_config=types.ThinkingConfig(thinking_budget=gemini_thinking_budget),
        ),
    )
    output = getattr(response, "text", "")
    if not output:
        raise RuntimeError("Gemini returned an empty response.")
    return str(output)


def _summarize_gemini_rest(
    text: str,
    *,
    model: str,
    api_key: str,
    system: str,
    max_output_tokens: int,
    temperature: float,
    gemini_thinking_budget: int,
    max_retries: int,
    timeout: int,
    sleep: RetrySleep = time.sleep,
) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "maxOutputTokens": max_output_tokens,
            "temperature": temperature,
            "thinkingConfig": {"thinkingBudget": gemini_thinking_budget},
        },
    }
    data = _post_with_retries(
        url,
        payload,
        api_key=api_key,
        timeout=timeout,
        max_retries=max_retries,
        sleep=sleep,
        params={"key": api_key},
    )
    try:
        return str(data["candidates"][0]["content"]["parts"][0]["text"])
    except (KeyError, IndexError, TypeError) as exc:
        message = data.get("error", {}).get("message", "Gemini returned no summary")
        raise RuntimeError(_scrub_secret(str(message), api_key)) from exc


def _summarize_claude(
    text: str,
    *,
    model: str,
    api_key: str,
    system: str,
    max_output_tokens: int,
    temperature: float,
) -> str:
    try:
        import anthropic
    except Exception as exc:
        raise RuntimeError(
            "Install the Claude extra: pip install 'youtube-summarizer[claude]'"
        ) from exc
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        system=system,
        messages=[{"role": "user", "content": text}],
        max_tokens=max_output_tokens,
        temperature=temperature,
    )
    parts = [getattr(block, "text", "") for block in response.content]
    output = "\n".join(part for part in parts if part)
    if not output:
        raise RuntimeError("Claude returned an empty response.")
    return output


def _summarize_openai(
    text: str,
    *,
    model: str,
    api_key: str,
    system: str,
    max_output_tokens: int,
    temperature: float,
    base_url: str | None,
) -> str:
    try:
        from openai import OpenAI
    except Exception as exc:
        raise RuntimeError(
            "Install the OpenAI extra: pip install 'youtube-summarizer[openai]'"
        ) from exc
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
        max_tokens=max_output_tokens,
        temperature=temperature,
    )
    output = response.choices[0].message.content
    if not output:
        raise RuntimeError("OpenAI returned an empty response.")
    return output


def _post_with_retries(
    url: str,
    payload: dict[str, Any],
    *,
    api_key: str,
    timeout: int,
    max_retries: int,
    sleep: RetrySleep = time.sleep,
    params: dict[str, str] | None = None,
) -> dict[str, Any]:
    for attempt in range(max_retries + 1):
        response = requests.post(url, params=params, json=payload, timeout=timeout)
        if response.status_code == 429 and attempt < max_retries:
            sleep(20 * (attempt + 1))
            continue
        if response.status_code in {500, 502, 503, 504} and attempt < max_retries:
            sleep(10 * (2**attempt))
            continue
        if response.ok:
            data = response.json()
            if isinstance(data, dict):
                return data
            raise RuntimeError("Provider returned a non-object JSON response.")
        message = _scrub_secret(response.text[:500], api_key)
        raise RuntimeError(f"Provider request failed with HTTP {response.status_code}: {message}")
    raise RuntimeError("Provider request failed after retries.")


def _scrub_secret(text: str, secret: str) -> str:
    return text.replace(secret, "[redacted]") if secret else text
