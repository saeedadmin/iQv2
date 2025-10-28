# Dockerfile for Telegram Bot
FROM python:3.12.5-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ make cmake \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright dependencies
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

# Expose port 8080
EXPOSE 8080

# Start the bot
CMD ["python", "core/telegram_bot.py"]