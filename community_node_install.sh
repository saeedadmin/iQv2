#!/bin/bash

# Community Node Installation Script for n8n
# Add these environment variables to your Render service

echo "Adding Community Node environment variables to Render..."

# These will be added to Render environment variables
cat << EOF

N8N_COMMUNITY_PACKAGES=["@telepilotco/n8n-nodes-telepilot"]

N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=false

N8N_RUNNERS_ENABLED=true

N8N_BLOCK_ENV_ACCESS_IN_NODE=false

N8N_GIT_NODE_DISABLE_BARE_REPOS=true

EOF

echo "Environment variables to add:"
echo "N8N_COMMUNITY_PACKAGES=[\"@telepilotco/n8n-nodes-telepilot\"]"
echo ""
echo "Steps:"
echo "1. Go to your Render dashboard"
echo "2. Select your n8n service"
echo "3. Go to Environment tab"
echo "4. Add the variable: N8N_COMMUNITY_PACKAGES"
echo "5. Value: [\"@telepilotco/n8n-nodes-telepilot\"]"
echo "6. Save and redeploy"
echo ""
echo "After redeployment, wait 5 minutes for installation to complete"