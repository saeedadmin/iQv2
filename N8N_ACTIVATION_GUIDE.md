# 🔧 N8N Workflow Activation Guide

## ✅ Current Status
- **N8N Server**: ✅ Running at https://iqv2.onrender.com
- **Webhook**: ✅ Accessible (IP issue fixed)
- **Telegram Bot Token**: ✅ Available
- **Workflow ID**: 5b347b5d-8f35-45b3-a499-de95153088f0
- **Status**: ⏳ **Workflow needs manual activation**

## 🎯 Next Steps to Complete Setup

### Step 1: Access N8N Interface
1. Go to: https://iqv2.onrender.com
2. Login with your credentials (basic auth)

### Step 2: Navigate to Workflow
1. In the N8N interface, look for your workflow
2. The workflow ID is: `5b347b5d-8f35-45b3-a499-de95153088f0`
3. Or navigate directly to: https://iqv2.onrender.com/workflows/5b347b5d-8f35-45b3-a499-de95153088f0

### Step 3: Activate Workflow
1. Look for a toggle switch in the top-right corner
2. Click to activate the workflow (turn it ON)
3. You should see "Active" status

### Step 4: Test Telegram Bot
1. Send a message to your Telegram bot: @YourBotName
2. The bot should process your message through N8N workflow
3. You should receive an AI-generated image

## 🔍 Testing Webhook (Optional)
After activation, you can test the webhook directly:

```bash
curl -X POST "https://iqv2.onrender.com/webhook/5b347b5d-8f35-45b3-a499-de95153088f0/webhook" \
  -H "Content-Type: application/json" \
  -d '{"message": {"message_id": 123, "from": {"id": 327459477, "is_bot": false}, "chat": {"id": 327459477, "type": "private"}, "text": "generate image"}}'
```

## 🎉 Expected Result
Once activated:
- ✅ Workflow will process Telegram messages
- ✅ Generate AI images using your configured AI service
- ✅ Send images back to Telegram users

## ⚠️ If You Still See IP Error
If you still get the "IP address 0.0.0.0 is reserved" error after activation:
1. Check that all N8N environment variables are set correctly
2. Restart the N8N service (manual redeployment)
3. Verify the webhook URL configuration

---
**Current Success**: The IP address issue has been resolved! ✅