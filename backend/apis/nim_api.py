import os
import time
import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv()

NIM_CHAT_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL_NAME = "mistralai/mistral-nemotron"  # verified live against NVIDIA's account-scoped catalogue; many listed NIM models 404


def generate_disease_info(query: str) -> str:
    # NVIDIA's gateway for this model caps generation around ~30-35s regardless of client
    # timeout (either hangs then drops, or returns its own 500). max_tokens=600 keeps
    # generation consistently in the 15-25s range; retries cover transient NVIDIA-side
    # 500s/timeouts on this community-hosted model.
    last_error = None
    for attempt in range(3):
        if attempt > 0:
            time.sleep(1.5)
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
                timeout=45,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            last_error = e
    raise last_error
