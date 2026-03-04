# Frontend Environment Configuration

## 📋 Overview

The frontend is configured to use environment variables for flexible deployment across different environments (development, staging, production).

---

## 🚀 Quick Setup

### 1. **Copy Environment Template**
```bash
cd frontend
cp .env.example .env
```

### 2. **Update `.env` for Your Environment**

#### For Production (Already Configured)
```env
REACT_APP_BACKEND_URL=https://task-tracker-production-2750.up.railway.app
REACT_APP_APP_NAME=Task Tracker
REACT_APP_VERSION=1.0.0
```

#### For Local Development
```env
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_APP_NAME=Task Tracker
REACT_APP_VERSION=1.0.0
```

#### For Docker Development
```env
REACT_APP_BACKEND_URL=http://backend:8001
REACT_APP_APP_NAME=Task Tracker
REACT_APP_VERSION=1.0.0
```

### 3. **Start the Frontend**
```bash
npm install
npm start
```

---

## 📁 File Structure

```
frontend/
├── .env                          # ← Environment variables (NOT in git)
├── .env.example                  # Template for .env
├── src/
│   ├── config/
│   │   └── api.js               # ← Centralized API configuration
│   ├── contexts/
│   │   └── AuthContext.js       # Updated to use API config
│   └── pages/
│       ├── Login.js
│       ├── Dashboard.js
│       └── ...
```

---

## 🔧 API Configuration File

The `src/config/api.js` file centralizes all API endpoints and configuration:

```javascript
import { API_CONFIG } from '../config/api';

// Access API configuration
API_CONFIG.API_URL          // Full API URL
API_CONFIG.AUTH.LOGIN      // Login endpoint path
API_CONFIG.TASKS.LIST      // Tasks list endpoint path
API_CONFIG.buildApiUrl()   // Helper to build full URLs
API_CONFIG.buildWsUrl()    // Helper for WebSocket URLs
```

### Usage Examples:

```javascript
// In components
import { API_CONFIG, buildApiUrl } from '../config/api';
import axios from 'axios';

// Get full URL
const loginUrl = buildApiUrl(API_CONFIG.AUTH.LOGIN);

// Make API calls
const response = await axios.get(
  buildApiUrl(API_CONFIG.TASKS.LIST)
);
```

---

## 📊 Environment Variables

All available environment variables:

| Variable | Purpose | Example |
|----------|---------|---------|
| `REACT_APP_BACKEND_URL` | **Required** - Backend API URL | `https://api.example.com` |
| `REACT_APP_APP_NAME` | App display name | `Task Tracker` |
| `REACT_APP_VERSION` | App version | `1.0.0` |
| `REACT_APP_ANALYTICS_ID` | Google Analytics ID | (optional) |
| `REACT_APP_SENTRY_DSN` | Error tracking | (optional) |
| `REACT_APP_ENABLE_DEBUG_MODE` | Debug mode | `false` |

---

## 🔀 Environment-Specific Configurations

### Development
```env
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_ENABLE_DEBUG_MODE=true
```

### Staging
```env
REACT_APP_BACKEND_URL=https://staging-api.example.com
REACT_APP_ENABLE_DEBUG_MODE=false
```

### Production
```env
REACT_APP_BACKEND_URL=https://task-tracker-production-2750.up.railway.app
REACT_APP_ENABLE_DEBUG_MODE=false
```

---

## 🐳 Docker Deployment

### Build for Production
```bash
docker build -f frontend/Dockerfile -t task-tracker-frontend .
```

### Environment Variables in Docker
Pass environment variables during build or runtime:

```bash
docker run \
  -e REACT_APP_BACKEND_URL=https://api.example.com \
  task-tracker-frontend
```

Or in `docker-compose.yml`:
```yaml
services:
  frontend:
    build: ./frontend
    environment:
      - REACT_APP_BACKEND_URL=https://api.example.com
```

---

## 🔐 Security Best Practices

✅ **DO:**
- ✅ Use HTTPS URLs in production
- ✅ Keep `.env` out of version control
- ✅ Use environment-specific configurations
- ✅ Rotate API keys regularly
- ✅ Never commit sensitive data

❌ **DON'T:**
- ❌ Commit `.env` files
- ❌ Use hardcoded URLs
- ❌ Share `.env` in messages
- ❌ Use test credentials in production
- ❌ Store secrets in source code

---

## 🧪 Testing Configuration

### Verify Environment Variables
```javascript
// In browser console or component:
console.log(process.env.REACT_APP_BACKEND_URL);
console.log(process.env.REACT_APP_APP_NAME);
```

### Check API Connection
```bash
# Test backend health check
curl https://task-tracker-production-2750.up.railway.app/api/health
```

---

## 🚀 Deployment Checklist

- [ ] `.env` file is in `.gitignore`
- [ ] `.env.example` is committed (without secrets)
- [ ] `REACT_APP_BACKEND_URL` points to correct backend
- [ ] Environment variables are set in deployment platform
- [ ] HTTPS is enabled for production
- [ ] CORS is properly configured in backend
- [ ] API health check passes

---

## 📞 Troubleshooting

### API Connection Issues
```javascript
// Check what URL is being used
import { API_CONFIG } from './config/api';
console.log('API URL:', API_CONFIG.API_URL);
```

### Variables Not Loading
1. Restart dev server: `npm start`
2. Check `.env` file exists
3. Variables must start with `REACT_APP_`
4. Restart terminal/IDE if environment changed

### CORS Errors
1. Verify backend CORS_ORIGINS includes frontend URL
2. Check backend is running
3. Ensure `REACT_APP_BACKEND_URL` is correct

---

## 📚 Learn More

- [Create React App - Environment Variables](https://create-react-app.dev/docs/adding-custom-environment-variables/)
- [12 Factor App - Configuration](https://12factor.net/config)
- [React Best Practices](https://react.dev/learn)

---

**Setup complete! 🎉**

Your frontend is now configured to work with the production backend at:
```
https://task-tracker-production-2750.up.railway.app
```

Start the frontend with: `npm start`
