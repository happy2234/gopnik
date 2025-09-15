# 🚨 QUICK PAT TOKEN FIX

Your GitHub Actions are failing with permission errors. Here's the fastest fix:

## 🎯 **Immediate Action Required**

### **Step 1: Create New PAT Token (2 minutes)**

1. **Go to**: https://github.com/settings/tokens
2. **Click**: "Generate new token (classic)"
3. **Name**: `Gopnik Full Access`
4. **Expiration**: `No expiration`
5. **Check ALL these boxes**:
   ```
   ✅ repo
   ✅ workflow  
   ✅ write:packages
   ✅ read:packages
   ```
6. **Click**: "Generate token"
7. **Copy the token** (you won't see it again!)

### **Step 2: Update Repository Secret (1 minute)**

1. **Go to**: https://github.com/happy2234/gopnik/settings/secrets/actions
2. **Find**: `PAT_TOKEN` 
3. **Click**: "Update"
4. **Paste**: Your new token
5. **Click**: "Update secret"

### **Step 3: Test the Fix (1 minute)**

1. **Go to**: https://github.com/happy2234/gopnik/actions
2. **Find**: "Setup GitHub Wiki" workflow
3. **Click**: "Run workflow" → "Run workflow"
4. **Wait**: Should complete without errors

## 🔍 **If Still Failing**

Run this test locally:
```bash
./scripts/test-pat-token.sh YOUR_TOKEN_HERE
```

## 🆘 **Common Issues**

### **"Permission denied to happy2234"**
- Token doesn't have `repo` scope
- Token expired
- Wrong token in secrets

### **"Wiki clone failed"**
- Wiki not enabled in repository settings
- Go to: https://github.com/happy2234/gopnik/settings
- Enable "Wikis" feature

### **"Still getting 403"**
- Delete old token completely
- Create fresh token with ALL permissions
- Make sure secret name is exactly `PAT_TOKEN`

## ✅ **Success Indicators**

When fixed, you'll see:
- ✅ Workflows complete without errors
- ✅ Wiki gets updated automatically  
- ✅ Status files are committed
- ✅ No more 403 permission errors

---

**⏰ This should take less than 5 minutes to fix!**