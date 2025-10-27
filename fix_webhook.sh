#!/bin/bash
# Webhook URL Fix and Test Script

WORKFLOW_ID="ff17baeb-3182-41c4-b60a-e6159b02023b"
WEBHOOK_URL="https://iqv2.onrender.com/webhook/${WORKFLOW_ID}/webhook"
BOT_TOKEN="1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc"

echo "🔧 N8N Webhook URL Fix & Test"
echo "================================"
echo "Workflow ID: $WORKFLOW_ID"
echo "Expected Webhook: $WEBHOOK_URL"
echo ""

# Test webhook endpoint
echo "🔍 Testing webhook endpoint..."
RESPONSE=$(curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"message": {"message_id": 123, "from": {"id": 327459477}, "chat": {"id": 327459477}, "text": "test"}}' \
  -w "\nHTTP_CODE:%{http_code}\n" \
  -s)

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
RESPONSE_BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE:")

echo "📊 Webhook Response:"
echo "   Status Code: $HTTP_CODE"
echo "   Response: $RESPONSE_BODY"
echo ""

# Test webhook registration
echo "🤖 Checking Telegram webhook registration..."
TELEGRAM_INFO=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo" | jq -r '.result.url // "Not registered"')
echo "   Telegram Webhook: $TELEGRAM_INFO"

if [[ "$TELEGRAM_INFO" == *iqv2.onrender.com* ]]; then
    echo "   ✅ Telegram webhook is correctly registered!"
else
    echo "   ❌ Telegram webhook registration issue!"
fi

echo ""

# Check N8N interface status
echo "🌐 Checking N8N interface..."
N8N_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://iqv2.onrender.com)
echo "   N8N Status: $N8N_STATUS"

if [ "$N8N_STATUS" == "200" ]; then
    echo "   ✅ N8N is accessible"
else
    echo "   ❌ N8N not accessible"
fi

echo ""
echo "📋 RECOMMENDED STEPS:"
echo "1. Go to: https://iqv2.onrender.com/workflows/$WORKFLOW_ID"
echo "2. Open the Telegram Bot trigger node"
echo "3. Check webhook URL in node settings"
echo "4. Replace 'localhost:8443' with 'iqv2.onrender.com:8443'"
echo "5. Save and activate the workflow"
echo "6. Test with: curl -X POST '$WEBHOOK_URL' ..."

echo ""
echo "🧪 Quick Test Commands:"
echo "Test webhook manually:"
echo "curl -X POST '$WEBHOOK_URL' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"message\": {\"message_id\": 123, \"from\": {\"id\": 327459477}, \"chat\": {\"id\": 327459477}, \"text\": \"generate landscape\"}}'"

echo ""
echo "Check Telegram bot status:"
echo "curl 'https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo'"