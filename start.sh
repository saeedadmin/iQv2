#!/bin/bash
# Startup script برای Koyeb

echo "🚀 Starting Telegram Bot..."
echo "📂 Current directory: $(pwd)"
echo "🐍 Python version: $(python --version)"
echo "📦 Installing dependencies..."

# Install dependencies
pip install -r requirements.txt

echo "🤖 Starting bot..."
python telegram_bot.py