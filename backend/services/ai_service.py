from __future__ import annotations

import os
import re
from pathlib import Path

from openai import OpenAI


ROOT_DIR = Path(__file__).resolve().parents[2]
SECRETS_FILE = ROOT_DIR / ".streamlit" / "secrets.toml"


def load_deepseek_api_key() -> str:
    env_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if env_key:
        return env_key

    if not SECRETS_FILE.exists():
        return ""

    content = SECRETS_FILE.read_text(encoding="utf-8")
    match = re.search(r'DEEPSEEK_API_KEY\s*=\s*"([^"]+)"', content)
    return match.group(1).strip() if match else ""


def stream_chat(messages: list[dict], temperature: float = 1.1):
    api_key = load_deepseek_api_key()
    if not api_key:
        raise RuntimeError("Missing DEEPSEEK_API_KEY.")

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    stream = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=True,
        temperature=temperature,
    )
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content


def respond_chat(messages: list[dict], temperature: float = 1.1) -> str:
    api_key = load_deepseek_api_key()
    if not api_key:
        raise RuntimeError("Missing DEEPSEEK_API_KEY.")

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content or ""
