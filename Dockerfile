FROM python:3.12-slim

# Install system dependencies required by Playwright Chromium
RUN apt-get update && apt-get install -y \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    wget \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libnspr4 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency listing first for caching
COPY requirements.txt pyproject.toml* ./

RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium

# Copy project files
COPY . .

# Expose default port (if using webhook server)
EXPOSE 8000

CMD ["python", "core/telegram_bot.py"]
