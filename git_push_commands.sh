#!/bin/bash
# Git commands to push package.json changes with TelePilot

echo "📦 Adding updated package.json to git..."
git add package.json

echo "💬 Committing changes with meaningful message..."
git commit -m "🚀 Add TelePilot community node for crypto signal monitoring

- Added @telepilotco/n8n-nodes-telepilot v0.5.2 to dependencies
- Enables Telegram UserBot functionality for crypto signal monitoring
- Compatible with n8n v1.117.0"

echo "🔄 Pushing changes to GitHub..."
git push origin main

echo "✅ Done! Changes pushed to GitHub successfully!"
echo ""
echo "📋 Next steps:"
echo "1. ✅ Git push completed"
echo "2. 🔄 Wait for Render auto-deployment (2-3 minutes)"
echo "3. 🔧 Add environment variables in Render dashboard"
echo "4. ✅ Test TelePilot installation"