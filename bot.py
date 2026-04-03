import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from config import Config
from utils.database import db
from utils.stream_server import start_web_server
import logging

logging.basicConfig(level=logging.INFO)

app = Client(
    "file_link_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="handlers")
)

@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    db.add_user(user_id)
    
    # Check for referral
    text = message.text
    if len(text.split()) > 1:
        referrer_id_str = text.split()[1]
        if referrer_id_str.isdigit() and int(referrer_id_str) != user_id:
            success, r_id = db.add_referral(user_id, int(referrer_id_str))
            if success:
                try:
                    await client.send_message(
                        int(referrer_id_str), 
                        "🎉 **Success!** Someone joined using your link.\n"
                        "🎁 You've been rewarded with **+15 extra downloads**!"
                    )
                    await message.reply_text("👋 **Welcome!** You joined via a referral link.")
                except: pass

    welcome_text = (
        "👋 **Welcome to the Premium File Link Bot!**\n\n"
        "Send or forward any file and I'll generate a high-speed direct download link for you.\n\n"
        "📜 **Bot Menu:**\n"
        "• /my - Check statistics & referral link\n"
        "• /how - How to use this bot\n"
        "• /rules - Usage rules and daily limits\n"
        "• /about - Bot information"
    )
    
    await message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 My Stats", callback_data="my_stats"), InlineKeyboardButton("📢 Updates", url=Config.SUPPORT_LINK)],
            [InlineKeyboardButton("❓ How It Works", callback_data="how"), InlineKeyboardButton("⚖️ Rules", callback_data="rules")]
        ])
    )

@app.on_message(filters.command("my") & filters.private)
async def my_stats_cmd(client, message):
    await show_user_stats(client, message.from_user.id, message)

@app.on_callback_query(filters.regex("my_stats"))
async def my_stats_callback(client, callback_query):
    await show_user_stats(client, callback_query.from_user.id, callback_query.message, edit=True)

async def show_user_stats(client, user_id, message, edit=False):
    res = db.get_user_data(user_id)
    if not res: extra_limit, total_ref, ref_by, count = (0, 0, None, 0)
    else: extra_limit, total_ref, ref_by, count = res
    
    bot_username = (await client.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    
    ref_by_text = f"👤 Referred by: `{ref_by}`" if ref_by else "👤 Referred by: `None`"
    
    stats_text = (
        "👤 **User Statistics**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 Daily Base Limit: `{Config.DAILY_LIMIT}`\n"
        f"🎁 Bonus Limit: `{extra_limit}`\n"
        f"📊 Total Limit: `{Config.DAILY_LIMIT + extra_limit}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Referrals: `{total_ref}`\n"
        f"{ref_by_text}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 **Your Referral Link:**\n`{ref_link}`\n\n"
        "*(Invite friends and get +15 limit per referral!)*"
    )
    
    if edit:
        await message.edit_text(stats_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_home")]]))
    else:
        await message.reply_text(stats_text)

@app.on_message(filters.command(["how", "howtowork"]) & filters.private)
async def how_command(client, message):
    text = (
        "❓ **How It Works**\n\n"
        "1. **Forward** a file or **Upload** it to this chat.\n"
        "2. Wait for the bot to generate a **Streaming Link**.\n"
        "3. Click **High Speed Download** to get your file instantly.\n\n"
        "💡 **Tip:** Files are streamed directly from Telegram servers for maximum speed!"
    )
    await message.reply_text(text)

@app.on_callback_query(filters.regex("how"))
async def how_callback(client, callback_query):
    text = (
        "❓ **How It Works**\n\n"
        "1. **Forward** a file or **Upload** it to this chat.\n"
        "2. Wait for the bot to generate a **Streaming Link**.\n"
        "3. Click **High Speed Download** to get your file instantly.\n\n"
        "💡 **Tip:** Files are streamed directly from Telegram servers for maximum speed!"
    )
    await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_home")]]))

@app.on_message(filters.command("rules") & filters.private)
async def rules_cmd(client, message):
    rules_text = (
        "📜 **Bot Usage Rules**\n\n"
        f"1️⃣ Default daily limit is **{Config.DAILY_LIMIT}** files per user.\n"
        "2️⃣ Referral link gives you **+15 downloads** per successful invite.\n"
        "3️⃣ Abuse or spam will result in a permanent ban.\n"
        "4️⃣ Files up to 20GB are supported."
    )
    await message.reply_text(rules_text)

@app.on_message(filters.command("about") & filters.private)
async def about_command(client, message):
    text = (
        "🤖 **About This Bot**\n\n"
        "This bot provides high-speed direct download links for Telegram files.\n\n"
        "🚀 **Key Features:**\n"
        "• Support up to 2GB files\n"
        "• Privacy focused (No local storage)\n"
        "• Instant streaming technology\n\n"
        f"✨ **Developed by:** {Config.DEVELOPER}"
    )
    await message.reply_text(text)

@app.on_message(filters.command("admin") & filters.user(Config.ADMIN_ID))
async def admin_panel(client, message):
    t_users, t_refs = db.get_admin_stats()
    text = (
        "🛠 **Admin Command Center**\n\n"
        f"📊 **Total Users:** `{t_users}`\n"
        f"👥 **Total Referrals:** `{t_refs}`\n\n"
        "**Available Commands:**\n"
        "• `/stats` - View professional bot stats\n"
        "• `/broadcast [text]` - Send announcement to all users\n"
        "• `/users` - List all registered user IDs\n"
        "• `/set_banner [script]` - Set HTML Banner (e.g., Adsterra)\n"
        "• `/set_interstitial [script]` - Set Interstitial script\n"
        "• `/set_smartlink [url]` - Set Smart Link / Direct Link\n"
        "• `/del_ads` - Clear all web advertisements"
    )
    await message.reply_text(text)

@app.on_message(filters.command("stats") & filters.user(Config.ADMIN_ID))
async def stats_command(client, message):
    t_users, t_refs = db.get_admin_stats()
    text = (
        "📊 **Bot Real-time Statistics**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Total Users: `{t_users}`\n"
        f"🔗 Total Referrals: `{t_refs}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "*(Data reflects all users who have ever messaged the bot)*"
    )
    await message.reply_text(text)

@app.on_message(filters.command("id"))
async def get_my_id(client, message):
    await message.reply_text(f"Your Telegram ID: `{message.from_user.id}`")

@app.on_message(filters.command("broadcast"))
async def broadcast_command(client, message):
    # Debugging: Check if user is admin
    if message.from_user.id != Config.ADMIN_ID:
        return await message.reply_text(
            f"❌ **Access Denied!**\n\n"
            f"Your Telegram ID: `{message.from_user.id}`\n"
            f"Set Admin ID: `{Config.ADMIN_ID}`\n\n"
            "Please make sure your ID matches the `ADMIN_ID` in the `.env` file."
        )

    if not message.reply_to_message and len(message.text.split()) < 2:
        return await message.reply_text("❌ **Format:** `/broadcast [message]` or reply to a message.")
    
    broadcast_msg = message.reply_to_message if message.reply_to_message else message.text.split(None, 1)[1]
    
    users = db.get_all_users()
    if not users:
        return await message.reply_text("⚠️ **No users found in database!**")

    status = await message.reply_text(f"📡 **Broadcasting to {len(users)} users...**")
    
    success = 0
    failed = 0
    
    for user_id in users:
        try:
            if message.reply_to_message:
                await broadcast_msg.copy(user_id)
            else:
                await client.send_message(user_id, broadcast_msg)
            success += 1
            await asyncio.sleep(0.05) # Slightly faster
        except Exception as e:
            failed += 1
    
    await status.edit_text(
        "✅ **Broadcast Completed!**\n\n"
        f"🚀 Successful: `{success}`\n"
        f"❌ Failed: `{failed}`\n"
        f"📊 Total Users: `{len(users)}`"
    )

@app.on_message(filters.command("set_banner") & filters.user(Config.ADMIN_ID))
async def set_banner_cmd(client, message):
    if len(message.text.split()) < 2: return await message.reply_text("❌ Provide Banner Script!")
    script = message.text.split(None, 1)[1]
    db.set_setting("banner_ad", script)
    await message.reply_text("✅ Banner Ad updated!")

@app.on_message(filters.command("set_interstitial") & filters.user(Config.ADMIN_ID))
async def set_inter_cmd(client, message):
    if len(message.text.split()) < 2: return await message.reply_text("❌ Provide Script!")
    script = message.text.split(None, 1)[1]
    db.set_setting("interstitial_ad", script)
    await message.reply_text("✅ Interstitial Ad updated!")

@app.on_message(filters.command("set_smartlink") & filters.user(Config.ADMIN_ID))
async def set_smart_cmd(client, message):
    if len(message.text.split()) < 2: return await message.reply_text("❌ Provide URL!")
    url = message.text.split(None, 1)[1]
    db.set_setting("smart_link", url)
    await message.reply_text("✅ Smart Link updated!")

@app.on_message(filters.command("del_ads") & filters.user(Config.ADMIN_ID))
async def del_ads_cmd(client, message):
    db.set_setting("banner_ad", None)
    db.set_setting("interstitial_ad", None)
    db.set_setting("smart_link", None)
    await message.reply_text("🗑 All Web Ads cleared!")

@app.on_message(filters.command("users") & filters.user(Config.ADMIN_ID))
async def list_users_cmd(client, message):
    users = db.get_all_users()
    text = "👤 **List of Registered Users:**\n\n"
    text += "\n".join([f"• `{uid}`" for uid in users[:50]]) # Limit to first 50
    if len(users) > 50:
        text += f"\n\n... and {len(users)-50} more."
    await message.reply_text(text)

@app.on_callback_query(filters.regex("back_home"))
async def back_home_callback(client, callback_query):
    await callback_query.message.delete()
    await start_command(client, callback_query.message)

async def main():
    await app.start()
    await start_web_server(app)
    print("Bot is fully online with Advanced UI and Referral System!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
