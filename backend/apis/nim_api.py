import os
import time
import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv()

NIM_CHAT_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL_NAME = "mistralai/mistral-nemotron"  # verified live against NVIDIA's account-scoped catalogue; many listed NIM models 404

DEADLINE_SECONDS = 35  # total wall-clock budget across attempts; normal answers take 15-25s
COOLDOWN_SECONDS = 120  # after a full failure, skip NIM briefly so an outage fails instantly
MAX_ATTEMPTS = 2

# Per-process; each worker tracks its own outage state, which is fine for a fail-fast hint.
_last_failure_at = None


def generate_disease_info(query: str) -> str:
    global _last_failure_at

    if _last_failure_at is not None and time.monotonic() - _last_failure_at < COOLDOWN_SECONDS:
        raise RuntimeError("NVIDIA NIM failed recently; skipping to fallback")

    deadline = time.monotonic() + DEADLINE_SECONDS
    last_error = None

    for attempt in range(MAX_ATTEMPTS):
        remaining = deadline - time.monotonic()
        if remaining < 8:
            break
        try:
            response = requests.post(
                NIM_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {os.getenv('NVIDIA_API_KEY')}",
                    "Accept": "application/json",
                },
                json={
                    "model": MODEL_NAME,
                    "messages": [{"role": "user", "content": query}],
                    "temperature": 0.5,
                    "top_p": 1,
                    "max_tokens": 600,
                    "stream": False,
                },
                timeout=remaining,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            _last_failure_at = None
            return content
        except requests.exceptions.RequestException as e:
            last_error = e
            time.sleep(1)

    _last_failure_at = time.monotonic()
    raise last_error or RuntimeError("NVIDIA NIM request budget exhausted")
