import aiohttp
from config import Config

class LinkGenerator:
    @staticmethod
    async def get_direct_link(file_id: str) -> str:
        """
        Fetches the file_path from Telegram Bot API and returns a direct download link.
        """
        if not Config.BOT_TOKEN:
            return None
        
        url = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/getFile?file_id={file_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        file_path = data["result"].get("file_path")
                        if file_path:
                            return f"https://api.telegram.org/file/bot{Config.BOT_TOKEN}/{file_path}"
                return None
