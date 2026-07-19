"""Minimal DeepSeek chat helper shared by pipeline utilities."""
import os
from pathlib import Path

import requests

DEEPSEEK = "https://api.deepseek.com/chat/completions"


def api_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        for line in (Path.home() / "scholarstack" / ".env").read_text().splitlines():
            if line.startswith("LLM_BINDING_API_KEY="):
                key = line.split("=", 1)[1]
    return key


def chat(prompt: str, model: str = "deepseek-v4-flash", temperature: float = 0.3) -> str:
    r = requests.post(
        DEEPSEEK,
        headers={"Authorization": f"Bearer {api_key()}"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}],
              "temperature": temperature},
        timeout=300,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]
