# 🔧 N8N Workflow Activation Steps

## 🎯 Goal: Turn ON your workflow

## 📋 Step-by-Step Guide

### Step 1: Access N8N
1. Open your browser
2. Go to: `https://iqv2.onrender.com`
3. Login with your credentials

### Step 2: Find Your Workflow
**Option A - Direct Link (Easiest):**
```
https://iqv2.onrender.com/workflows/ff17baeb-3182-41c4-b60a-e6159b02023b
```

**Option B - Navigate:**
1. Click "Workflows" in left menu
2. Find your workflow in the list
3. Click on it to open

### Step 3: Look for Activation Controls

#### 🔴 Wrong State (INACTIVE):
- Toggle switch shows **OFF** or **🔴**
- May say "Inactive", "Draft", or "Paused"
- Webhook will return 403 Forbidden

#### 🟢 Correct State (ACTIVE):
- Toggle switch shows **ON** or **🟢**  
- May say "Active" or "Running"
- Webhook will return 200 OK

### Step 4: Common Locations for Toggle

**Location 1: Top Toolbar**
```
[🔴 OFF] [Save] [Test] [Execute] [Workflow Name]
                  ↑
                  Look for this toggle
```

**Location 2: Right Panel**
```
Workflow Settings
├─ Active: [🔴] [Toggle ON/OFF]
├─ Name: Your Workflow Name
└─ ...
```

**Location 3: Below Workflow Title**
```
Your Workflow Name
[🔴 OFF] [Edit] [Share]
     ↑
     This toggle
```

**Location 4: Workflow Editor**
```
┌─ [🔴 OFF] Workflow Name ─┐
│                         │
│  Nodes...               │
└─────────────────────────┘
```

### Step 5: Activate
1. **Click the toggle** to turn it ON
2. **Save the workflow** (Ctrl+S or Save button)
3. **Verify it shows ON/Active**

## 🚨 If You Can't Find the Toggle

### Check These:

**1. Are you in Edit Mode?**
- Click "Edit" if you see it
- Toggle may only be visible in edit mode

**2. Look for "Activate" Button:**
- Some interfaces use "Activate" instead of toggle
- Button might be in toolbar

**3. Check Workflow Status:**
- Right-click on workflow in list
- Look for "Activate" option

**4. Settings Panel:**
- Workflow settings or preferences
- Look for "Status" or "Active" option

## 🔄 After Activation

### Immediate Test:
```bash
# Run this test after activation:
python test_after_activation.py
```

### Expected Result:
```
✅ SUCCESS! Workflow is ACTIVE and working!
🎉 Webhook accepted the request
```

## 📱 Then Test the Bot

1. Send message to your bot: `"generate a beautiful landscape"`
2. Should get AI image response
3. Check N8N Executions tab for workflow runs

## 🎯 What Changes After Activation

**Before (Inactive):**
- Telegram sends webhook → 403 Forbidden ❌
- Bot doesn't respond ❌

**After (Active):**  
- Telegram sends webhook → 200 OK ✅
- Workflow executes ✅
- AI image generated ✅
- Bot sends image back ✅

## 🆘 If Still Not Working

**Check List:**
- [ ] Workflow shows ACTIVE/ON
- [ ] Workflow is saved (Ctrl+S)
- [ ] Telegram trigger node has correct webhook URL
- [ ] Test again with test script

**Still Getting 403?**
- Refresh the N8N page
- Double-check toggle is ON
- Try deactivating and reactivating