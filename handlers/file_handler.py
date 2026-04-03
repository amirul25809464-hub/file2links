import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from config import Config
from utils.database import db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def humanbytes(size):
    if not size: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

@Client.on_message(filters.private & filters.media)
async def handle_file(client: Client, message: Message):
    user_id = message.from_user.id
    
    try:
        # 1. Force Subscription Check (Supports multiple channels separated by comma)
        if Config.FORCE_SUB_CHANNEL:
            channels = [c.strip() for c in Config.FORCE_SUB_CHANNEL.split(",") if c.strip()]
            for channel in channels:
                try:
                    await client.get_chat_member(channel, user_id)
                except UserNotParticipant:
                    buttons = []
                    for idx, ch in enumerate(channels):
                        buttons.append([InlineKeyboardButton(f"📢 Join Channel {idx+1}", url=f"https://t.me/{ch.replace('@','')}")])
                    buttons.append([InlineKeyboardButton("🔄 I Have Joined", callback_data="check_join")])
                    
                    return await message.reply_text(
                        "✋ **Access Denied!**\n\nTo use this bot, you must join our update channels. "
                        "This helps us keep the service alive for everyone!",
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )
                except Exception as e:
                    logger.error(f"F-Sub error: {e}")

        # 2. Daily Limit Check
        is_admin = (user_id == Config.ADMIN_ID)
        allowed, used_count, total_limit, extra_info = db.check_user(user_id, Config.DAILY_LIMIT)
        
        if not allowed and not is_admin:
            return await message.reply_text(
                f"🚫 **Daily Limit Reached!**\n\n"
                f"You have used your limit of `{total_limit}` files today.\n"
                f"⏳ **Reset In:** `{extra_info}`\n\n"
                "💡 **Unlock more?** Refer a friend and get **+15 downloads** instantly!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎁 Refer & Get +15", callback_data="my_stats")],
                    [InlineKeyboardButton("🛠 Support", url=Config.SUPPORT_LINK)]
                ])
            )

        # 3. Stylish Loading Animation
        status_msg = await message.reply_text("⚡ **Initializing Stream...**")
        await asyncio.sleep(0.5)
        await status_msg.edit_text("🛰 **Scanning File...**\n`[▒▒▒▒▒▒▒▒▒▒] 0%`")
        await asyncio.sleep(0.4)
        await status_msg.edit_text("🛰 **Scanning File...**\n`[████▒▒▒▒▒▒] 40%`")
        await asyncio.sleep(0.4)
        await status_msg.edit_text("🛰 **Scanning File...**\n`[████████▒▒] 80%`")

        # 4. Media identification
        media = (message.video or message.document or message.audio or message.photo or message.voice or message.animation)
        file_id = media.file_id
        file_name = getattr(media, "file_name", "Media_File")
        file_size = getattr(media, "file_size", 0)
        
        # Track Global Statistics
        db.increment_global_stat("total_files", 1)
        db.increment_global_stat("total_file_size", file_size)
        
        # 5. Link Generation
        # IMPORTANT: We use the message.chat.id and message.id to ensure the stream server can find it.
        base = Config.DOMAIN.strip().rstrip('/')
        if base and not base.startswith("http"):
            base = f"https://{base}"
        if not base:
            base = f"http://localhost:{Config.PORT}"
            
        # Generate Short Link (Redirect System)
        slug = db.create_short_link(file_id, message.chat.id, message.id)
        streaming_link = f"{base}/s/{slug}"

        # 6. Final Animation Step
        await status_msg.edit_text("🚀 **Finalizing Link...**\n`[██████████] 100%`")
        await asyncio.sleep(0.3)
        
        # --- DO NOT DELETE THE ORIGINAL MESSAGE ---
        # If the message is deleted, the direct link will break with "Media not found".

        # 7. Professional Success UI
        rem_limit = "♾ Unlimited" if is_admin else (total_limit - used_count)
        
        # Check for active advertisement
        current_ad = db.get_setting("ad_message")
        ad_section = f"\n━━━━━━━━━━━━━━━━━━━━━━\n📢 **Ads:** {current_ad}" if current_ad else ""

        response_text = (
            "🚀 **Link Generated Successfully!**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📁 **File Name:** `{file_name}`\n"
            f"⚖️ **File Size:** `{humanbytes(file_size)}`\n"
            f"📊 **Today's Remaining:** `{rem_limit}` files\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔗 **Direct Secure Link:**\n"
            f"└ `{streaming_link}`\n"
            f"{ad_section}\n\n"
            f"✨ **Powered by:** {Config.DEVELOPER}"
        )
        
        await status_msg.edit_text(
            response_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📥 High Speed Download", url=streaming_link)],
                [InlineKeyboardButton("🛠 Support", url=Config.SUPPORT_LINK), InlineKeyboardButton("👥 Refer Friends (+15)", callback_data="my_stats")]
            ])
        )

    except Exception as e:
        logger.error(f"Error handling file: {e}")
        await message.reply_text(f"❌ **An error occurred:** `{str(e)}`")

@Client.on_callback_query(filters.regex("check_join"))
async def check_join_callback(client, callback_query):
    user_id = callback_query.from_user.id
    channels = [c.strip() for c in Config.FORCE_SUB_CHANNEL.split(",") if c.strip()]
    
    joined = True
    for channel in channels:
        try:
            await client.get_chat_member(channel, user_id)
        except:
            joined = False
            break
            
    if joined:
        await callback_query.answer("✅ Success! Joining verified.", show_alert=True)
        await callback_query.message.delete()
    else:
        await callback_query.answer("⚠️ Please join all channels first!", show_alert=True)
