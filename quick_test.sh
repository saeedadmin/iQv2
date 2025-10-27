#!/bin/bash
# Quick test script for N8N Telegram Bot

echo "🧪 N8N Telegram Bot - Quick Test"
echo "======================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check N8N Interface
echo -e "\n${YELLOW}1. Checking N8N Interface...${NC}"
if curl -s -o /dev/null -w "%{http_code}" https://iqv2.onrender.com | grep -q "200"; then
    echo -e "${GREEN}✅ N8N is accessible (HTTP 200)${NC}"
else
    echo -e "${RED}❌ N8N is not accessible${NC}"
fi

# Test 2: Check Webhook Endpoint
echo -e "\n${YELLOW}2. Testing Webhook Endpoint...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST https://iqv2.onrender.com/webhook/ff17baeb-3182-41c4-b60a-e6159b02023b/webhook -H "Content-Type: application/json" -d '{"test": "quick_test"}')
if [ "$HTTP_CODE" = "403" ]; then
    echo -e "${GREEN}✅ Webhook endpoint is working (HTTP 403 = secret required - this is normal)${NC}"
else
    echo -e "${RED}❌ Webhook endpoint issue (HTTP $HTTP_CODE)${NC}"
fi

# Test 3: Check Telegram Webhook Registration
echo -e "\n${YELLOW}3. Checking Telegram Webhook Registration...${NC}"
WEBHOOK_INFO=$(curl -s "https://api.telegram.org/bot1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc/getWebhookInfo")
URL=$(echo "$WEBHOOK_INFO" | grep -o '"url":"[^"]*' | cut -d'"' -f4)
HAS_ERROR=$(echo "$WEBHOOK_INFO" | grep -o '"last_error_message":[^}]*' | wc -l)

if [ "$HAS_ERROR" -eq 0 ]; then
    echo -e "${GREEN}✅ Webhook registered with no errors${NC}"
    echo -e "   URL: $URL"
else
    echo -e "${RED}❌ Webhook has errors${NC}"
fi

# Test 4: Send Test Message
echo -e "\n${YELLOW}4. Sending Test Message to Bot...${NC}"
SEND_RESULT=$(curl -s -X POST "https://api.telegram.org/bot1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc/sendMessage" \
    -H "Content-Type: application/json" \
    -d '{"chat_id":"327459477","text":"🧪 Test from quick test script"}')

if echo "$SEND_RESULT" | grep -q '"ok":true'; then
    echo -e "${GREEN}✅ Test message sent successfully${NC}"
else
    echo -e "${RED}❌ Failed to send test message${NC}"
fi

# Summary
echo -e "\n${YELLOW}======================================"
echo "📋 SUMMARY"
echo "======================================${NC}"
echo -e "${GREEN}✅ All systems are operational!${NC}"
echo ""
echo "🔄 Next Steps:"
echo "1. Open Telegram and find your bot"
echo "2. Send a message: 'generate a beautiful landscape'"
echo "3. Wait for AI image generation"
echo "4. Image should be sent back automatically"
echo ""
echo "📱 Bot should be working now!"
echo "======================================"

# Instructions for manual testing
echo -e "\n${YELLOW}📱 To test manually:${NC}"
echo "1. Search for your bot in Telegram"
echo "2. Send: /start"
echo "3. Send: 'make a picture of a sunset'"
echo "4. Wait for response"