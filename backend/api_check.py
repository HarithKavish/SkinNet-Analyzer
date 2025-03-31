import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

API_KEY = os.getenv("API_KEY")

genai.configure(api_key=API_KEY)
models = genai.list_models()
for model in models:
    print(model.name)
