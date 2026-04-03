# Telegram File Direct Link Bot 🚀

A production-ready Telegram bot that converts forwarded or uploaded media files into direct download links instantly. Built with Python and Pyrogram.

## 🌟 Features

- **Fast Processing:** Generates direct links within 1–2 seconds.
- **Privacy Focused:** Does not store files locally; uses Telegram's servers.
- **Comprehensive Detection:** Supports Video, Audio, Document, Photo, Voice, Animation, and more.
- **Forward Support:** Works with files forwarded from channels, groups, or private chats.
- **Clean Interface:** Provides clear status messages and markdown-formatted links.

## 🛠 Tech Stack

- **Python 3.10+**
- **Framework:** Pyrogram
- **Concurrency:** asyncio
- **Environment:** python-dotenv
- **Networking:** aiohttp

## 📁 Project Structure

```text
telegram-file-link-bot/
├── bot.py             # Entry point
├── config.py          # Configuration manager
├── handlers/
│   └── file_handler.py # Media processing logic
├── utils/
│   └── link_generator.py # Bot API interaction
├── requirements.txt   # Dependencies
├── .env.example       # Example environment variables
└── README.md          # Documentation
```

## 🚀 Setup Guide

### 1. Create a Bot
1. Open [Telegram](https://t.me/BotFather) and search for **@BotFather**.
2. Start a chat and send `/newbot`.
3. Follow instructions to get your **BOT_TOKEN**.

### 2. Get API Credentials
1. Go to [my.telegram.org](https://my.telegram.org).
2. Log in with your phone number.
3. Click on **API development tools**.
4. Create a new application to get your **API_ID** and **API_HASH**.

### 3. Installation
Clone the repository (or copy the files) and install dependencies:

```bash
pip install -r requirements.txt
```

### 4. Configuration
1. Rename `.env.example` to `.env`.
2. Fill in your credentials:
```env
API_ID=123456
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
```

### 5. Running Locally
```bash
python bot.py
```

---

## 🌐 Deployment Guide

### **Railway (Recommended)**
1. Create a new project on [Railway](https://railway.app/).
2. Connect your GitHub repository.
3. Add **Environment Variables** (API_ID, API_HASH, BOT_TOKEN) in the project settings.
4. Railway will automatically detect the `requirements.txt` and start the bot.

### **Render**
1. Create a **Background Worker** on [Render](https://render.com/).
2. Connect your repository.
3. Set Environment Variables.
4. Set the start command: `python bot.py`.

### **Replit**
1. Create a new Repl.
2. Upload the files.
3. In the **Secrets** tab, add your environment variables.
4. Click **Run**.
5. *Tip: Use a "keep-alive" service like `UptimeRobot` to ping the Replit webview if you add a simple web server.*

---

## ⚠️ Security and Limitations

- **File Size:** Telegram Bots are limited to certain file sizes when retrieving `file_path`. Generally, files up to 20MB can be retrieved via `getFile`. For larger files, the bot might fail to get a direct link through this method.
- **Token:** The direct download link includes your bot token. Do not share these links publicly if you want to keep your token secret, or use a sacrificial bot.
- **Privacy:** If a file is from a private channel the bot isn't in, it might fail to process it.

## 🛡 License
MIT License. Free for all use.
