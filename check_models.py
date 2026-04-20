import os
from dotenv import load_dotenv
from google import genai

# Load your .env file
load_dotenv()

# Initialize the exact client LangChain is using under the hood
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

print("--- AVAILABLE FLASH MODELS ---")
for model in client.models.list():
    # Only print models that have "flash" in the name and support generation
    if "flash" in model.name and "generateContent" in model.supported_actions:
        print(model.name)
