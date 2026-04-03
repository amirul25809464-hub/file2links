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

        # Get global stats
        total_files, total_bytes = db.get_global_stats()
        total_users, _ = db.get_admin_stats()
        from handlers.file_handler import humanbytes
        total_data = humanbytes(total_bytes)

        # Get file info for the landing page
        message = await client.get_messages(int(chat_id), int(msg_id))
        
        # --- Expiration Logic ---
        import time
        from datetime import datetime
        now = time.time()
        msg_time = message.date.timestamp()
        expiration_limit = 3600 # 1 hour
        elapsed = now - msg_time
        
        if elapsed > expiration_limit:
            return web.Response(text="""
                <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><style>
                body { background: #0f172a; color: #f8fafc; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; text-align: center; }
                .msg { background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; padding: 20px; border-radius: 12px; }
                </style></head><body><div class="msg"><h1>🛑 Link Expired</h1><p>Links are only valid for 1 hour for security reasons.</p></div></body></html>
            """, content_type='text/html', status=410)
        
        remaining_seconds = int(expiration_limit - elapsed)

        media = (message.video or message.document or message.audio or 
                 message.photo or message.voice or message.animation)
        file_name = getattr(media, "file_name", "Telegram_File")
        file_size = humanbytes(getattr(media, "file_size", 0))

        direct_link = f"/dl/{file_id}?chat={chat_id}&msg={msg_id}"

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Download {file_name}</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
            <style>
                :root {{
                    --primary: #6366f1; --primary-hover: #4f46e5; --bg: #0f172a;
                    --card-bg: rgba(30, 41, 59, 0.7); --text: #f8fafc;
                    --text-dim: #94a3b8; --accent: #ef4444; --success: #10b981;
                }}
                * {{ box-sizing: border-box; margin: 0; padding: 0; }}
                body {{
                    font-family: 'Inter', sans-serif; background-color: var(--bg); color: var(--text);
                    display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; padding: 20px;
                }}
                .container {{ width: 100%; max-width: 550px; background: var(--card-bg); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 24px; padding: 40px 30px; text-align: center; }}
                
                .global-stats {{
                    display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 25px;
                    padding: 15px; background: rgba(0,0,0,0.2); border-radius: 16px;
                }}
                .stat-item {{ display: flex; flex-direction: column; gap: 4px; }}
                .stat-val {{ font-weight: 700; color: var(--success); font-size: 1.1rem; }}
                .stat-lbl {{ font-size: 10px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; }}

                h1 {{ font-size: 1.5rem; font-weight: 700; margin-bottom: 8px; word-break: break-all; }}
                .file-info {{ display: flex; align-items: center; justify-content: center; gap: 8px; color: var(--text-dim); margin-bottom: 12px; font-size: 0.95rem; }}
                
                .timer-box {{
                    display: inline-flex; align-items: center; gap: 6px; background: rgba(239, 68, 68, 0.1);
                    color: var(--accent); padding: 6px 12px; border-radius: 100px; font-size: 0.85rem; font-weight: 600; margin-bottom: 20px;
                }}

                .ad-slot {{ position: relative; width: 100%; background: rgba(15, 23, 42, 0.4); border-radius: 16px; padding: 12px; margin: 15px 0; min-height: 80px; }}
                .ad-label {{ position: absolute; top: 2px; left: 8px; font-size: 9px; color: rgba(255, 255, 255, 0.15); }}

                .download-btn {{
                    display: flex; align-items: center; justify-content: center; gap: 12px;
                    background: linear-gradient(135deg, var(--primary), var(--primary-hover)); color: white;
                    padding: 16px; border-radius: 14px; text-decoration: none; font-weight: 600; transition: 0.3s;
                }}
                .download-btn:hover {{ transform: translateY(-2px); }}
                
                .footer {{ margin-top: 30px; font-size: 0.8rem; color: var(--text-dim); }}
                .icon {{ width: 18px; height: 18px; fill: currentColor; opacity: 0.8; }}
            </style>
            {interstitial_ad}
        </head>
        <body>
            <div class="container">
                <div class="global-stats">
                    <div class="stat-item">
                        <span class="stat-val">{total_users}</span>
                        <span class="stat-lbl">Active Users</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-val">{total_files}</span>
                        <span class="stat-lbl">Files Served</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-val">{total_data}</span>
                        <span class="stat-lbl">Data Shared</span>
                    </div>
                </div>

                <h1>{file_name}</h1>
                <div class="file-info">Size: {file_size}</div>

                <div class="timer-box">
                    <span>Link Expires In: <span id="countdown">--:--</span></span>
                </div>

                <div class="ad-slot">{banner_ad}<span class="ad-label">ADVERTISEMENT</span></div>

                <a href="{direct_link}" class="download-btn" onclick="window.open('{smart_link}', '_blank');">
                    Start High Speed Download
                </a>

                <div class="ad-slot">{banner_ad}<span class="ad-label">ADVERTISEMENT</span></div>
            </div>
            <div class="footer">Powered by {Config.DEVELOPER}</div>

            <script>
                let timeLeft = {remaining_seconds};
                function updateTimer() {{
                    if (timeLeft <= 0) {{ location.reload(); return; }}
                    const minutes = Math.floor(timeLeft / 60);
                    const seconds = timeLeft % 60;
                    document.getElementById('countdown').textContent = `${{minutes.toString().padStart(2, '0')}}:${{seconds.toString().padStart(2, '0')}}`;
                    timeLeft--;
                }}
                setInterval(updateTimer, 1000); updateTimer();
            </script>
        </body>
        </html>
        """
        return web.Response(text=html_content, content_type='text/html')
    except Exception as e:
        return web.Response(text=f"Error: {e}", status=500)

async def media_streamer(request):
    client: Client = request.app['client']
    from utils.database import db
    file_id = request.match_info.get('file_id')
    chat_id = request.query.get("chat")
    msg_id = request.query.get("msg")
    
    if not chat_id or not msg_id:
        return web.Response(text="Error: Missing context.", status=400)
    
    try:
        message = await client.get_messages(int(chat_id), int(msg_id))
        media = (message.video or message.document or message.audio or 
                 message.photo or message.voice or message.animation)

        original_name = getattr(media, "file_name", "file")
        bot_username = request.app.get('bot_username', 'Bot')
        
        if "." in original_name:
            name, ext = original_name.rsplit(".", 1)
            new_name = f"{name}_@{bot_username}.{ext}"
        else:
            new_name = f"{original_name}_@{bot_username}"

        headers = {
            "Content-Type": getattr(media, "mime_type", "application/octet-stream"),
            "Content-Length": str(media.file_size),
            "Content-Disposition": f'attachment; filename="{new_name}"',
            "Accept-Ranges": "bytes",
        }

        response = web.StreamResponse(status=200, headers=headers)
        await response.prepare(request)

        downloaded_in_this_session = 0
        async for chunk in client.stream_media(message, limit=0):
            chunk_size = len(chunk)
            await response.write(chunk)
            downloaded_in_this_session += chunk_size
        
        # Update Global Bytes and Check Milestones
        old_total = int(db.get_setting("total_bytes", 0))
        new_total = db.increment_global_stat("total_bytes", downloaded_in_this_session)
        
        # 10GB Boundary check (10 * 1024 * 1024 * 1024 = 10,737,418,240)
        ten_gb = 10737418240
        if (new_total // ten_gb) > (old_total // ten_gb):
            await post_milestone(client, db, new_total)

        return response
    except Exception as e:
        logger.error(f"Streaming error: {{e}}")
        return web.Response(text=f"Server Error: {{str(e)}}", status=500)

async def post_milestone(client, db, total_bytes):
    if not Config.STATS_CHANNEL: return
    
    users, _ = db.get_admin_stats()
    from handlers.file_handler import humanbytes
    data_str = humanbytes(total_bytes)
    
    milestone_text = (
        "🎊 **New Milestone Reached!** 🎊\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 **Total Downloaded:** `{data_str}`\n"
        f"👤 **Active Users:** `{users}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 Thank you for choosing our Bot!\n"
        f"✨ **Developed by:** {Config.DEVELOPER}"
    )
    
    try:
        await client.send_message(Config.STATS_CHANNEL, milestone_text)
        print(f"✅ Milestone posted to {Config.STATS_CHANNEL}")
    except Exception as e:
        print(f"❌ Failed to post milestone: {e}")

async def start_web_server(client):
    app = web.Application()
    app['client'] = client

    # Get bot username once for renaming
    try:
        me = await client.get_me()
        app['bot_username'] = me.username
    except:
        app['bot_username'] = "FileBot"

    app.router.add_get('/download/{file_id}', landing_page)
    app.router.add_get('/dl/{file_id}', media_streamer)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', Config.PORT)
    await site.start()
    print(f"✅ Statistics & Milestone System Online on port {Config.PORT}")
