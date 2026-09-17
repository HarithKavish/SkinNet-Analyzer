import os
import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv()

NIM_CHAT_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL_NAME = "mistralai/mistral-nemotron"  # verified live against NVIDIA's account-scoped catalogue; many listed NIM models 404


def generate_disease_info(query: str) -> str:
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
            "max_tokens": 1024,
            "stream": False,
        },
        timeout=60,  # NIM community endpoints can cold-start a model instance on first call
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
