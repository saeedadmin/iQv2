# مراحل نهایی نصب TelePilot

## قدم 1: Package.json (انجام شد ✅)
TelePilot به package.json اضافه شد:
```json
"@telepilotco/n8n-nodes-telepilot": "^0.5.2"
```

## قدم 2: Git Commit & Push
```bash
git add package.json
git commit -m "🚀 Add TelePilot community node for crypto signal monitoring"
git push origin main
```

## قدم 3: Environment Variable در Render
در Render Dashboard اضافه کن:
```
Name: N8N_COMMUNITY_PACKAGES
Value: ["@telepilotco/n8n-nodes-telepilot"]
```

## قدم 4: Deploy & Wait
- Render خودکار auto-deploy می‌کنه
- صبر کن 5-10 دقیقه

## قدم 5: Verification
### در n8n چک کن:
1. **Settings → Community Nodes**
   ```
   @telepilotco/n8n-nodes-telepilot (INSTALLED)
   ```

2. **New Workflow → Add Node**
   ```
   TelePilot Trigger
   TelePilot Action
   ```

## خروجی مورد انتظار
```
✅ Package installed: @telepilotco/n8n-nodes-telepilot v0.5.2
✅ Build successful
✅ n8n ready
✅ TelePilot nodes available
```

## اگه خطا شد
- **Logs چک کن** برای detailed errors
- **Environment variable syntax** verify کن
- **Package version** چک کن (0.5.2 latest)

## خلاصه
- ✅ Package.json: Done
- ⏳ Git Push: Your turn  
- ⏳ Environment Variable: Your turn
- ⏳ Deploy: Render will handle
- ⏳ Test: After deployment

**Ready to proceed?** 🚀