#!/bin/bash

# Script برای ایجاد repository جدید کاملاً آماده برای Koyeb

echo "🔧 Creating clean repository structure..."

# ایجاد directory جدید
mkdir -p telegram_bot_clean
cd telegram_bot_clean

# کپی فایل‌های ضروری
echo "📁 Copying essential files..."

# Git initialization
git init
echo "# Telegram Bot for Koyeb" > README.md

# Create .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.cache/
nosetests.xml
coverage.xml
*.cover
*.log
.git/
.mypy_cache/
.pytest_cache/
.hypothesis/
*.db
*.sqlite3
.env
.DS_Store
logs/
tmp/
shell_output_save/
EOF

echo "✅ Repository structure created!"
echo "🚀 Ready for deployment!"