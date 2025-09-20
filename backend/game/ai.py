from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

print("Gemini API Key Loaded:", API_KEY is not None)

def generate_story(prompt):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": API_KEY}
    data = {"contents": [{"parts":[{"text": prompt}]}]}
    
    r = requests.post(url, headers=headers, params=params, json=data)
    if r.status_code == 200:
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return "The storyteller faltered..."
