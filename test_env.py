from dotenv import load_dotenv
import os

load_dotenv()

elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')
if elevenlabs_key:
    print(f"✅ ELEVENLABS_API_KEY loaded: {elevenlabs_key[:20]}...")
else:
    print("❌ ELEVENLABS_API_KEY not found")
