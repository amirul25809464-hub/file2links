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
            <link href="https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap" rel="stylesheet">
            <style>
                :root {{
                    --bg: #0d1117;
                    --card: #161b22;
                    --border: #30363d;
                    --text: #c9d1d9;
                    --text-bright: #f0f6fc;
                    --btn-bg: #238636;
                    --btn-hover: #2ea043;
                    --link: #58a6ff;
                }}
                * {{ box-sizing: border-box; margin: 0; padding: 0; }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
                    background-color: var(--bg);
                    color: var(--text);
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    padding: 16px;
                }}
                .stats-discrete {{
                    display: flex; gap: 12px; margin-bottom: 20px; font-size: 12px;
                }}
                .stat-tag {{ 
                    background: #21262d; border: 1px solid var(--border); 
                    padding: 4px 12px; border-radius: 6px; color: #8b949e;
                    display: flex; align-items: center; gap: 6px;
                }}

                .box {{
                    width: 100%;
                    max-width: 550px;
                    background: var(--card);
                    border: 1px solid var(--border);
                    border-radius: 6px;
                }}
                .box-header {{
                    background: #21262d; 
                    padding: 16px; 
                    border-bottom: 1px solid var(--border);
                    display: flex; align-items: center; gap: 10px;
                    border-top-left-radius: 6px; border-top-right-radius: 6px;
                }}
                .box-header h2 {{ font-size: 14px; font-weight: 600; color: var(--text-bright); }}
                
                .box-body {{ padding: 32px; text-align: center; }}
                h1 {{ font-size: 20px; font-weight: 600; color: var(--text-bright); margin-bottom: 8px; word-break: break-all; }}
                .meta {{ font-size: 14px; color: #8b949e; margin-bottom: 24px; }}
                
                .timer-box {{
                    display: inline-block;
                    background: rgba(210, 153, 34, 0.1); border: 1px solid rgba(210, 153, 34, 0.2); 
                    color: #d29922; padding: 6px 12px; border-radius: 6px; 
                    font-size: 12px; font-weight: 600; margin-bottom: 24px;
                }}

                .ad-placeholder {{
                    background: #0d1117; border: 1px dashed var(--border); border-radius: 6px;
                    padding: 12px; margin: 16px 0; min-height: 90px;
                    position: relative;
                }}
                .ad-label {{ position: absolute; top: 4px; left: 8px; font-size: 9px; color: #484f58; }}

                .btn-primary {{
                    display: block; width: 100%; 
                    background-color: var(--btn-bg); color: #fff;
                    padding: 12px; border-radius: 6px; text-decoration: none;
                    text-align: center; font-size: 14px; font-weight: 600;
                    border: 1px solid rgba(240,246,252,0.1); transition: 0.2s;
                }}
                .btn-primary:hover {{ background-color: var(--btn-hover); }}
                
                .secondary-link {{
                    display: inline-block; margin-top: 16px; color: var(--link);
                    text-decoration: none; font-size: 13px;
                }}
                .secondary-link:hover {{ text-decoration: underline; }}

                .footer {{ margin-top: 32px; font-size: 12px; color: #8b949e; }}
                
                @media (max-width: 480px) {{
                    .box-body {{ padding: 24px 16px; }}
                    h1 {{ font-size: 18px; }}
                }}
            </style>
            {interstitial_ad}
        </head>
        <body>
            <div class="stats-discrete">
                <div class="stat-tag">
                    <svg height="12" width="12" viewBox="0 0 16 16" fill="currentColor"><path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0Zm4 8c0 1.11-.89 2-2 2H4c-1.11 0-2-.89-2-2 0-2.04 2.29-3.27 4.13-3.71l.15-.04c.15-.04.3-.06.45-.08.15-.02.3-.03.45-.03.15 0 .3.01.45.03.15.02.3.04.45.08l.15.04c1.84.44 4.13 1.67 4.13 3.71Z"></path></svg>
                    {disp_users}
                </div>
                <div class="stat-tag">
                    <svg height="12" width="12" viewBox="0 0 16 16" fill="currentColor"><path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75V1.5h-8a1 1 0 0 0-1 1V13a1 1 0 0 0 1 1H7a.75.75 0 0 1 0 1.5H4.5A2.5 2.5 0 0 1 2 13V2.5Zm3.75 7a.75.75 0 0 1 .75-.75h3a.75.75 0 0 1 0 1.5h-3a.75.75 0 0 1-.75-.75Zm0-3a.75.75 0 0 1 .75-.75h3a.75.75 0 0 1 0 1.5h-3a.75.75 0 0 1-.75-.75Z"></path><path d="M5 11.75a.75.75 0 0 1 .75-.75h2a.75.75 0 0 1 0 1.5h-2a.75.75 0 0 1-.75-.75Z"></path></svg>
                    {disp_files}
                </div>
            </div>

            <div class="box">
                <div class="box-header">
                    <svg height="16" width="16" viewBox="0 0 16 16" fill="#8b949e"><path d="M10.5 1.75v3.25h3.25l-3.25-3.25ZM9 1.75L15.25 8v5.25A1.75 1.75 0 0 1 13.5 15H2.5A1.75 1.75 0 0 1 .75 13.25V2.75C.75 1.784 1.534 1 2.5 1H9v.75ZM2.5 2.5a.25.25 0 0 0-.25.25v10.5c0 .138.112.25.25.25h11a.25.25 0 0 0 .25-.25V8.5H9.75a.75.75 0 0 1-.75-.75V2.5H2.5Z"></path></svg>
                    <h2>File Storage Distribution</h2>
                </div>

                <div class="box-body">
                    <h1>{file_name}</h1>
                    <p class="meta">Size: {file_size_human} • Handled {disp_data} data globally</p>
                    
                    <div>
                        <span class="timer-box">⚠ Link expires in <span id="clock">--:--</span></span>
                    </div>

                    <div class="ad-placeholder">
                        <span class="ad-label">ADVERTISEMENT</span>
                        {banner_ad}
                    </div>

                    <a href="{direct_link}" class="btn-primary" onclick="window.open('{smart_link}', '_blank');">
                        Download Now
                    </a>

                    <a href="{smart_link}" class="secondary-link">Direct High Speed Stream</a>

                    <div class="ad-placeholder">
                        <span class="ad-label">ADVERTISEMENT</span>
                        {banner_ad}
                    </div>
                </div>
            </div>

            <div class="footer">
                © {Config.DEVELOPER} • Shared Distribution Network
            </div>

            <script>
                let sec = {remaining_seconds};
                function tick() {{
                    if (sec <= 0) {{ location.reload(); return; }}
                    const m = Math.floor(sec / 60); const s = sec % 60;
                    document.getElementById('clock').textContent = `${{m.toString().padStart(2, '0')}}:${{s.toString().padStart(2, '0')}}`;
                    sec--;
                }}
                setInterval(tick, 1000); tick();
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

async def short_redirect(request):
    slug = request.match_info.get('slug')
    from utils.database import db
    data = db.get_short_link(slug)
    if not data:
        return web.Response(text="Error: Link not found or expired.", status=404)
    
    file_id, chat_id, msg_id = data
    target_url = f"/download/{file_id}?chat={chat_id}&msg={msg_id}"
    return web.HTTPFound(location=target_url)

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

    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', Config.PORT)
    await site.start()
    print(f"✅ Statistics & Milestone System Online on port {Config.PORT}")
