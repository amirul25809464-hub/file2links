import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

class Config:
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    
    # Port & Domain
    PORT = int(os.getenv("PORT", 8080))
    DOMAIN = os.getenv("DOMAIN", "")
    
    # --- New Features ---
    # Your Telegram ID (Get it from @MissRose_bot using /id)
    ADMIN_ID = int(os.getenv("ADMIN_ID", 0)) 
    # Channel username (e.g., @MyChannel)
    FORCE_SUB_CHANNEL = os.getenv("FORCE_SUB_CHANNEL", "") 
    # Channel for milestone stats
    STATS_CHANNEL = os.getenv("STATS_CHANNEL", "")
    # Max files a user can download per day
    DAILY_LIMIT = int(os.getenv("DAILY_LIMIT", 5))
    
    # Custom Info
    _support = os.getenv("SUPPORT_LINK", "https://t.me/avriox")
    SUPPORT_LINK = _support if _support.startswith("http") else f"https://t.me/{_support.replace('@','')}"
    
    DEVELOPER = os.getenv("DEVELOPER", "@avriox")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "")

    # Final check
    if not all([API_ID, API_HASH, BOT_TOKEN]):
        print("Error: Required environment variables are missing.")
        print("Please check your .env file or environment.")
