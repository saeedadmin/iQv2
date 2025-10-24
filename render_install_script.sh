#!/bin/bash

# TelePilot Community Node Installation Script for Render
# Add these environment variables to your Render service

echo "🚀 TelePilot Installation via Render Environment Variables"
echo "=================================================="

# Environment Variables to add to Render
echo "📋 Environment Variables to Add:"
echo ""
echo "Variable 1 (Primary):"
echo "Name: N8N_COMMUNITY_PACKAGES"
echo "Value: [\"@telepilotco/n8n-nodes-telepilot\"]"
echo ""

echo "Variable 2:"
echo "Name: N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS"
echo "Value: false"
echo ""

echo "Variable 3:"
echo "Name: N8N_RUNNERS_ENABLED" 
echo "Value: true"
echo ""

echo "Variable 4:"
echo "Name: N8N_BLOCK_ENV_ACCESS_IN_NODE"
echo "Value: false"
echo ""

echo "Variable 5 (Optional - for debugging):"
echo "Name: N8N_LOG_LEVEL"
echo "Value: debug"
echo ""

echo "🔧 Steps to follow:"
echo "1. Go to https://dashboard.render.com"
echo "2. Find your iqv2-n8n-bot service"
echo "3. Click on the service"
echo "4. Go to 'Environment' tab"
echo "5. Add each variable above"
echo "6. Click 'Save Changes'"
echo "7. Wait 5-10 minutes for deployment"
echo ""

echo "✅ Success Indicators:"
echo "- Render logs show: 'Community package installed successfully'"
echo "- n8n Settings → Community Nodes shows installed package"
echo "- Add Node dialog includes 'TelePilot' options"
echo ""

echo "🛠️ If installation fails, try:"
echo "1. Remove all variables"
echo "2. Add just N8N_COMMUNITY_PACKAGES first"
echo "3. Deploy and wait"
echo "4. Add remaining variables if needed"
echo ""

echo "Alternative Manual Installation:"
echo "If environment variables don't work, try SSH into container:"
echo "cd /usr/src/app && npm install @telepilotco/n8n-nodes-telepilot"