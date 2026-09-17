from google import genai
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Configure the Gemini API
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-flash-latest"  # tracks Google's current flash model, avoids re-pinning on retirement

def gemini(query):
    return client.models.generate_content(model=MODEL_NAME, contents=query)