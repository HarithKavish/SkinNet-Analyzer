import google.generativeai as ai
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Configure the Gemini API
ai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = ai.GenerativeModel("gemini-1.5-flash")
chat = model.start_chat()

def gemini(query):
    return chat.send_message(query)