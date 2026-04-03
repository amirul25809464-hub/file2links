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
        real_files, real_file_size, real_bytes = db.get_global_stats()
        real_users, _ = db.get_admin_stats()
        from handlers.file_handler import humanbytes
        
        # Professional "Booster" stats for authority
        disp_users = f"{real_users + 124508:,}"
        disp_files = f"{real_files + 980420:,}"
        disp_data = humanbytes(real_bytes + (5.8 * 1024 * 1024 * 1024 * 1024))

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
                body { background: #030712; color: #f8fafc; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; text-align: center; }
                .msg { background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.2); padding: 40px; border-radius: 24px; max-width: 400px; }
                h1 { color: #ef4444; margin-bottom: 15px; font-size: 1.5rem; }
                p { color: #9ca3af; font-size: 0.9rem; line-height: 1.5; }
                </style></head><body><div class="msg"><h1>Link Expired</h1><p>Links expire after 1 hour. Please head back to @avriox bot for a fresh link.</p></div></body></html>
            """, content_type='text/html', status=410)
        
        remaining_seconds = int(expiration_limit - elapsed)

        media = (message.video or message.document or message.audio or 
                 message.photo or message.voice or message.animation)
        file_name = getattr(media, "file_name", "Telegram_File")
        file_size_human = humanbytes(getattr(media, "file_size", 0))

        direct_link = f"/dl/{file_id}?chat={chat_id}&msg={msg_id}"

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Download {file_name}</title>
            <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">
            <style>
                :root {{
                    --primary: #8b5cf6;
                    --bg: #030712;
                    --card: #0b0f1a;
                    --text: #f9fafb;
                    --text-dim: #9ca3af;
                    --success: #10b981;
                    --error: #ef4444;
                }}
                * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Outfit', sans-serif; }}
                body {{
                    background: var(--bg);
                    color: var(--text);
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    padding: 24px;
                }}
                .top-stats {{
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 12px;
                    width: 100%;
                    max-width: 500px;
                    margin-bottom: 20px;
                    background: rgba(255, 255, 255, 0.02);
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    padding: 16px;
                    border-radius: 20px;
                }}
                .s-box {{ text-align: center; }}
                .s-val {{ display: block; font-weight: 700; color: var(--success); font-size: 0.95rem; }}
                .s-lbl {{ display: block; color: var(--text-dim); font-size: 0.6rem; text-transform: uppercase; margin-top: 4px; font-weight: 700; letter-spacing: 0.05em; }}

                .container {{
                    width: 100%;
                    max-width: 500px;
                    background: var(--card);
                    border: 1px solid rgba(255, 255, 255, 0.03);
                    border-radius: 32px;
                    padding: 48px 32px;
                    text-align: center;
                    box-shadow: 0 40px 100px -20px rgba(0, 0, 0, 0.8);
                }}
                
                h1 {{ font-size: 1.6rem; word-break: break-all; margin-bottom: 8px; line-height: 1.2; font-weight: 700; }}
                .file-meta {{ color: var(--text-dim); font-size: 0.9rem; margin-bottom: 24px; font-weight: 500; }}
                
                .timer {{
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    background: rgba(239, 68, 68, 0.05);
                    color: var(--error);
                    padding: 6px 14px;
                    border-radius: 100px;
                    font-size: 0.85rem;
                    font-weight: 600;
                    margin-bottom: 32px;
                    border: 1px solid rgba(239, 68, 68, 0.1);
                }}

                .ad-wrap {{
                    background: rgba(0, 0, 0, 0.2);
                    border-radius: 20px;
                    padding: 16px;
                    margin: 24px 0;
                    position: relative;
                    min-height: 100px;
                }}
                .ad-tag {{ position: absolute; top: 6px; left: 12px; font-size: 8px; color: rgba(255, 255, 255, 0.1); font-weight: 700; }}

                .btn {{
                    display: block;
                    background: var(--primary);
                    color: white;
                    padding: 20px;
                    border-radius: 18px;
                    text-decoration: none;
                    font-weight: 600;
                    font-size: 1.1rem;
                    transition: 0.3s;
                    box-shadow: 0 10px 20px rgba(139, 92, 246, 0.2);
                }}
                .btn:hover {{ transform: translateY(-3px); box-shadow: 0 15px 30px rgba(139, 92, 246, 0.3); }}
                
                .direct {{ display: inline-block; margin-top: 24px; color: var(--primary); text-decoration: none; font-size: 0.9rem; font-weight: 600; }}

                .footer {{ margin-top: 40px; font-size: 0.75rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; }}

                @media (max-width: 480px) {{
                    .container {{ padding: 40px 24px; }}
                    h1 {{ font-size: 1.4rem; }}
                }}
            </style>
            {interstitial_ad}
        </head>
        <body>
            <div class="top-stats">
                <div class="s-box">
                    <span class="s-val">{disp_users}</span>
                    <span class="s-lbl">Active Users</span>
                </div>
                <div class="s-box">
                    <span class="s-val">{disp_files}</span>
                    <span class="s-lbl">Cloud Files</span>
                </div>
                <div class="s-box">
                    <span class="s-val">{disp_data}</span>
                    <span class="s-lbl">Bandwidth</span>
                </div>
            </div>

            <div class="container">
                <h1>{file_name}</h1>
                <div class="file-meta">Size: {file_size_human}</div>

                <div class="timer">
                    ⏱️ Expires in <span id="clock">--:--</span>
                </div>

                <div class="ad-wrap">
                    <span class="ad-tag">SPONSORED</span>
                    {banner_ad}
                </div>

                <a href="{direct_link}" class="btn" onclick="window.open('{smart_link}', '_blank');">
                    📥 Start Fast Download
                </a>

                <a href="{smart_link}" class="direct">🚀 Instant Stream (No Wait)</a>

                <div class="ad-wrap">
                    <span class="ad-tag">SPONSORED</span>
                    {banner_ad}
                </div>
            </div>

            <div class="footer">
                Developed by {Config.DEVELOPER}
            </div>

            <script>
                let sec = {remaining_seconds};
                function tick() {{
                    if (sec <= 0) {{ location.reload(); return; }}
                    const m = Math.floor(sec / 60);
                    const s = sec % 60;
                    document.getElementById('clock').textContent = `${{m.toString().padStart(2, '0')}}:${{s.toString().padStart(2, '0')}}`;
                    sec--;
                }}
                setInterval(tick, 1000); tick();
            </script>
        </body>
        </html>
        """
        return web.Response(text=html_content, content_type='text/html')
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

    app.router.add_get('/s/{slug}', short_redirect)
    app.router.add_get('/download/{file_id}', landing_page)
    app.router.add_get('/dl/{file_id}', media_streamer)

async def short_redirect(request):
    slug = request.match_info.get('slug')
    from utils.database import db
    data = db.get_short_link(slug)
    if not data:
        return web.Response(text="Error: Link not found or expired.", status=404)
    
    file_id, chat_id, msg_id = data
    target_url = f"/download/{file_id}?chat={chat_id}&msg={msg_id}"
    return web.HTTPFound(location=target_url)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', Config.PORT)
    await site.start()
    print(f"✅ Statistics & Milestone System Online on port {Config.PORT}")
