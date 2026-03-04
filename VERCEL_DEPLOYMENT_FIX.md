# 🚀 Fix Vercel Deployment CORS Error

## ❌ Problem

Your Vercel-deployed frontend gets a CORS error:

```
Access to XMLHttpRequest at 'http://localhost:8000/api/auth/login'
has been blocked by CORS policy
```

**Why?**
- Your frontend on Vercel tries to call `localhost:8000`
- `localhost` only exists on your computer
- Vercel servers can't access your local machine
- Browser blocks the request → CORS error

---

## ✅ Solution (3 Steps)

### Step 1: Add Environment Variable to Vercel

1. **Go to Vercel Dashboard:**
   ```
   https://vercel.com/dashboard
   ```

2. **Select your project:** `task-tracker` (or similar)

3. **Go to Settings:**
   - Click "Settings" tab
   - Click "Environment Variables"

4. **Add New Variable:**
   ```
   Name:  REACT_APP_BACKEND_URL
   Value: https://task-tracker-production-2750.up.railway.app
   ```

5. **Click "Save"**

6. **Redeploy:**
   - Go to "Deployments" tab
   - Click the three dots on latest deployment
   - Select "Redeploy"

---

### Step 2: Update Backend CORS

**Already Done!** ✅

Updated `backend/.env`:
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://task-tracker-git-main-anjalis-projects-eb3c2b0a.vercel.app
```

**Next:** Push this change to your backend on Railway

---

### Step 3: Deploy Updated Backend

**Option 1: If using Railway (Recommended)**
```bash
# 1. Commit the change
git add backend/.env
git commit -m "Update CORS for Vercel frontend domain"

# 2. Push to GitHub
git push origin main

# 3. Railway auto-deploys from GitHub
# (Wait 2-3 minutes for deployment)
```

**Option 2: Manual Deploy**
```bash
# Restart backend on Railway dashboard:
# 1. Go to https://railway.app
# 2. Select your project
# 3. Click "Redeploy"
```

---

## 🔍 How It Works Now

```
Vercel Frontend
https://task-tracker-git-main-anjalis-projects-eb3c2b0a.vercel.app
        |
        | Uses REACT_APP_BACKEND_URL env variable
        | (https://task-tracker-production-2750.up.railway.app)
        |
        ↓
Railway Backend
https://task-tracker-production-2750.up.railway.app
        |
        | CORS allows Vercel domain ✅
        |
        ↓
     MongoDB Atlas
```

---

## ✅ Verify It Works

### Test Login
1. Open your Vercel deployed site
2. Go to login page
3. Login with test credentials:
   - Email: `admin@tripstars.com`
   - Password: `Admin@123`
4. ✅ Should work now!

### Check Console
```javascript
// Open browser DevTools (F12)
// Console tab should show:
console.log(process.env.REACT_APP_BACKEND_URL)
// Should output:
// https://task-tracker-production-2750.up.railway.app
```

---

## 📋 Checklist

- [ ] Added `REACT_APP_BACKEND_URL` to Vercel Environment Variables
- [ ] Set value to `https://task-tracker-production-2750.up.railway.app`
- [ ] Redeployed on Vercel
- [ ] Updated backend `.env` with Vercel domain
- [ ] Pushed changes to GitHub
- [ ] Backend redeployed on Railway
- [ ] Tested login on Vercel - works! ✅

---

## 🆘 Still Getting CORS Error?

### Check 1: Verify Environment Variable in Vercel
```javascript
// In browser console on Vercel site:
console.log(process.env.REACT_APP_BACKEND_URL)
```

Should show: `https://task-tracker-production-2750.up.railway.app`

### Check 2: Verify Backend CORS
```bash
# Test CORS headers:
curl -i https://task-tracker-production-2750.up.railway.app/api/health
```

Look for header:
```
Access-Control-Allow-Origin: *
```

### Check 3: Hard Refresh Vercel
- Clear cache: `Ctrl+Shift+Delete`
- Hard refresh: `Ctrl+Shift+R`
- Redeploy on Vercel again

### Check 4: Check Backend Logs
```bash
# On Railway dashboard:
# 1. Select project
# 2. Click "Logs" tab
# 3. Check for errors
```

---

## 📝 Reference: Environment Variables

### Frontend (Vercel)
```
REACT_APP_BACKEND_URL=https://task-tracker-production-2750.up.railway.app
REACT_APP_APP_NAME=Task Tracker
REACT_APP_VERSION=1.0.0
```

### Backend (Railway)
```
MONGO_URL=mongodb+srv://tripstars:trip1234@cluster0.fqy0kzg.mongodb.net/
DB_NAME=task_tracker
JWT_SECRET_KEY=tripstars-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://task-tracker-git-main-anjalis-projects-eb3c2b0a.vercel.app
```

---

## 🎯 Summary

| Component | Location | Status |
|-----------|----------|--------|
| Frontend | Vercel | Deployed ✅ |
| Backend | Railway | Deployed ✅ |
| Database | MongoDB Atlas | Connected ✅ |
| CORS | Backend | Updated ✅ |
| Env Vars | Vercel | Need to set ⏳ |

---

**Once you complete Step 1 above, your CORS error will be fixed!** 🎉

Need help? Check the error in your browser console (F12) and let me know what it says.
