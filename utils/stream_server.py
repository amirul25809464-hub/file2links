from aiohttp import web
import logging
from config import Config
from pyrogram import Client
from pyrogram.types import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def landing_page(request):
    client: Client = request.app['client']
    from utils.database import db
    
    file_id = request.match_info.get('file_id')
    chat_id = request.query.get("chat")
    msg_id = request.query.get("msg")
    
    if not chat_id or not msg_id:
        return web.Response(text="Error: Context missing.", status=400)
    
    try:
        # Get ad scripts from DB
        banner_ad = db.get_setting("banner_ad", "<!-- No Banner Ad Set -->")
        interstitial_ad = db.get_setting("interstitial_ad", "<!-- No Interstitial Ad Set -->")
        smart_link = db.get_setting("smart_link", "#")

        # Get file info for the landing page
        message = await client.get_messages(int(chat_id), int(msg_id))
        media = (message.video or message.document or message.audio or 
                 message.photo or message.voice or message.animation)
        file_name = getattr(media, "file_name", "Telegram_File")
        from handlers.file_handler import humanbytes
        file_size = humanbytes(getattr(media, "file_size", 0))

        direct_link = f"/dl/{file_id}?chat={chat_id}&msg={msg_id}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Download {file_name}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: sans-serif; background-color: #0f172a; color: white; text-align: center; padding: 20px; }}
                .card {{ background: #1e293b; padding: 30px; border-radius: 15px; display: inline-block; max-width: 90%; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
                .btn {{ background: #3b82f6; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; margin-top: 20px; font-size: 18px; transition: 0.3s; }}
                .btn:hover {{ background: #2563eb; transform: scale(1.05); }}
                .ad-box {{ margin: 20px 0; min-height: 100px; background: rgba(255,255,255,0.05); border-radius: 8px; padding: 10px; }}
                .info {{ color: #94a3b8; font-size: 14px; margin-bottom: 20px; }}
                a.smart-link {{ color: #60a5fa; text-decoration: none; display: block; margin-top: 10px; font-size: 14px; }}
            </style>
            {interstitial_ad}
        </head>
        <body>
            <div class="card">
                <h2>{file_name}</h2>
                <div class="info">Size: {file_size}</div>
                
                <div class="ad-box">
                    {banner_ad}
                </div>

                <a href="{direct_link}" class="btn" onclick="window.open('{smart_link}', '_blank');">🚀 Start High Speed Download</a>
                
                <a href="{smart_link}" class="smart-link">Check out our sponsored content!</a>

                <div class="ad-box">
                    {banner_ad}
                </div>
            </div>
            
            <p style="color: #64748b; margin-top: 20px;">Powered by {Config.DEVELOPER}</p>
        </body>
        </html>
        """
        return web.Response(text=html_content, content_type='text/html')
    except Exception as e:
        return web.Response(text=f"Error: {e}", status=500)

async def media_streamer(request):
    client: Client = request.app['client']
    file_id = request.match_info.get('file_id')
    chat_id = request.query.get("chat")
    msg_id = request.query.get("msg")
    
    if not chat_id or not msg_id:
        return web.Response(text="Error: Direct link missing context.", status=400)
    
    try:
        message = await client.get_messages(int(chat_id), int(msg_id))
        media = (message.video or message.document or message.audio or 
                 message.photo or message.voice or message.animation)

        if not media:
            return web.Response(text="Error: No media found.", status=404)

        file_size = media.file_size
        file_name = getattr(media, "file_name", "downloaded_file")
        mime_type = getattr(media, "mime_type", "application/octet-stream")

        headers = {
            "Content-Type": mime_type,
            "Content-Length": str(file_size),
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Accept-Ranges": "bytes",
        }

        response = web.StreamResponse(status=200, headers=headers)
        await response.prepare(request)

        async for chunk in client.stream_media(message, limit=0):
            await response.write(chunk)

        return response
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        return web.Response(text=f"Server Error: {str(e)}", status=500)

async def start_web_server(client):
    app = web.Application()
    app['client'] = client
    app.router.add_get('/download/{file_id}', landing_page) # User first sees ads
    app.router.add_get('/dl/{file_id}', media_streamer)    # Actual file delivery
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', Config.PORT)
    await site.start()
    print(f"✅ Web Server started with Ad-Land Support on port {Config.PORT}")
