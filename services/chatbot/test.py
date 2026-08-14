import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is not set. Please configure it in a .env file.")
genai.configure(api_key=api_key)

for m in genai.list_models():
    print(m.name)