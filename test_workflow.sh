#!/bin/bash
# N8N Workflow Test Script
# Run this AFTER activating the workflow

WORKFLOW_ID="5b347b5d-8f35-45b3-a499-de95153088f0"
WEBHOOK_URL="https://iqv2.onrender.com/webhook/${WORKFLOW_ID}/webhook"

echo "🚀 Testing N8N Workflow..."
echo "Workflow ID: $WORKFLOW_ID"
echo "Webhook URL: $WEBHOOK_URL"
echo ""

# Test webhook with sample Telegram message
echo "📤 Sending test message to webhook..."
RESPONSE=$(curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "message_id": 123,
      "date": 1699999999,
      "chat": {
        "id": 327459477,
        "type": "private"
      },
      "from": {
        "id": 327459477,
        "is_bot": false,
        "first_name": "Test User"
      },
      "text": "generate a beautiful landscape image"
    }
  }' \
  -w "\nHTTP Status: %{http_code}\nResponse Time: %{time_total}s\n" \
  -s)

echo "🔍 Test Results:"
echo "$RESPONSE"
echo ""

# Check response
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP Status:" | cut -d' ' -f3)
RESPONSE_TIME=$(echo "$RESPONSE" | grep "Response Time:" | cut -d' ' -f3)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ SUCCESS! Webhook is working correctly!"
    echo "⏱️  Response time: ${RESPONSE_TIME}s"
    echo "🎉 The workflow should now process Telegram messages!"
elif [ "$HTTP_CODE" = "404" ]; then
    echo "⚠️  Workflow not activated yet"
    echo "📝 Please activate the workflow in N8N interface first"
    echo "🔗 Go to: https://iqv2.onrender.com/workflows/${WORKFLOW_ID}"
    echo "🎛️  Click the toggle to activate"
else
    echo "❌ Unexpected response"
    echo "🔍 HTTP Status: $HTTP_CODE"
fi

echo ""
echo "📱 Next steps:"
echo "1. If successful: Send message to your Telegram bot"
echo "2. The bot should process the message and generate an image"
echo "3. Check your Telegram chat for the AI-generated image"

# Optional: Test basic connectivity
echo ""
echo "🌐 Testing basic connectivity..."
curl -s -o /dev/null -w "Status: %{http_code}\nResponse Time: %{time_total}s\n" https://iqv2.onrender.com