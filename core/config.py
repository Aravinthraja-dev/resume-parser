import os
from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENV", "development")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not found in environment")
