# TripStars Task Management System - Deployment Guide

This guide covers deploying the TripStars application to production using **PM2**, **Nginx**, and **MongoDB Atlas**.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [MongoDB Atlas Setup](#mongodb-atlas-setup)
3. [Server Setup](#server-setup)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Nginx Configuration](#nginx-configuration)
7. [SSL Certificate (Let's Encrypt)](#ssl-certificate)
8. [PM2 Process Management](#pm2-process-management)
9. [Environment Variables Reference](#environment-variables-reference)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Ubuntu 20.04+ or similar Linux server
- Domain name pointed to your server
- Node.js 18+ and npm
- Python 3.10+
- Git

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Python 3.10+
sudo apt install -y python3 python3-pip python3-venv

# Install PM2 globally
sudo npm install -g pm2

# Install Nginx
sudo apt install -y nginx

# Install Certbot for SSL
sudo apt install -y certbot python3-certbot-nginx
```

---

## MongoDB Atlas Setup

### 1. Create Atlas Account
- Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
- Create a free account and a new cluster

### 2. Create Database User
1. Go to **Database Access** → **Add New Database User**
2. Choose **Password Authentication**
3. Set username and strong password
4. Set **Database User Privileges**: `Read and write to any database`
5. Click **Add User**

### 3. Configure Network Access
1. Go to **Network Access** → **Add IP Address**
2. For production, add your server's IP address
3. Or add `0.0.0.0/0` for access from anywhere (less secure)

### 4. Get Connection String
1. Go to **Database** → **Connect** → **Connect your application**
2. Copy the connection string:
```
mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/<dbname>?retryWrites=true&w=majority
```
3. Replace `<username>`, `<password>`, and `<dbname>` with your values

---

## Server Setup

### 1. Clone Repository

```bash
cd /var/www
sudo git clone <your-repo-url> tripstars
sudo chown -R $USER:$USER /var/www/tripstars
cd tripstars
```

### 2. Create Directory Structure

```bash
mkdir -p /var/www/tripstars/backend/uploads/chat
mkdir -p /var/www/tripstars/backend/uploads/attachments
chmod -R 755 /var/www/tripstars/backend/uploads
```

---

## Backend Deployment

### 1. Setup Python Virtual Environment

```bash
cd /var/www/tripstars/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create `/var/www/tripstars/backend/.env`:

```env
# MongoDB Atlas Connection
MONGO_URL=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
DB_NAME=tripstars_production

# JWT Configuration
JWT_SECRET=your-super-secure-jwt-secret-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (update with your domain)
CORS_ORIGINS=https://yourdomain.com

# Email Configuration (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@tripstars.com
```

### 3. Test Backend Locally

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Visit `http://your-server-ip:8001/api/health` to verify.

---

## Frontend Deployment

### 1. Install Dependencies

```bash
cd /var/www/tripstars/frontend
npm install
# or
yarn install
```

### 2. Configure Environment Variables

Create `/var/www/tripstars/frontend/.env.production`:

```env
REACT_APP_BACKEND_URL=https://yourdomain.com
```

### 3. Build for Production

```bash
npm run build
# or
yarn build
```

This creates a `build/` directory with static files.

---

## Nginx Configuration

### 1. Create Nginx Config

Create `/etc/nginx/sites-available/tripstars`:

```nginx
# Upstream for backend API
upstream tripstars_backend {
    server 127.0.0.1:8001;
    keepalive 32;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL certificates (will be configured by Certbot)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # Frontend static files
    root /var/www/tripstars/frontend/build;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # API routes - proxy to backend
    location /api {
        proxy_pass http://tripstars_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;  # For WebSocket connections
        
        # File upload size limit
        client_max_body_size 15M;
    }

    # WebSocket endpoint
    location /api/ws {
        proxy_pass http://tripstars_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }

    # Frontend routes - serve index.html for SPA
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 2. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/tripstars /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

---

## SSL Certificate

### 1. Obtain Certificate with Certbot

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 2. Auto-renewal

Certbot automatically sets up renewal. Test with:

```bash
sudo certbot renew --dry-run
```

---

## PM2 Process Management

### 1. Create PM2 Ecosystem File

Create `/var/www/tripstars/ecosystem.config.js`:

```javascript
module.exports = {
  apps: [
    {
      name: 'tripstars-backend',
      cwd: '/var/www/tripstars/backend',
      script: 'venv/bin/uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 8001 --workers 4',
      interpreter: 'none',
      env: {
        NODE_ENV: 'production'
      },
      // Restart settings
      max_restarts: 10,
      restart_delay: 1000,
      watch: false,
      // Logging
      error_file: '/var/log/tripstars/backend-error.log',
      out_file: '/var/log/tripstars/backend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    }
  ]
};
```

### 2. Create Log Directory

```bash
sudo mkdir -p /var/log/tripstars
sudo chown -R $USER:$USER /var/log/tripstars
```

### 3. Start Application

```bash
cd /var/www/tripstars
pm2 start ecosystem.config.js
```

### 4. Save PM2 Configuration

```bash
pm2 save
pm2 startup  # Follow the instructions to enable startup on boot
```

### 5. Useful PM2 Commands

```bash
# View status
pm2 status

# View logs
pm2 logs tripstars-backend

# Restart application
pm2 restart tripstars-backend

# Stop application
pm2 stop tripstars-backend

# Monitor
pm2 monit
```

---

## Environment Variables Reference

### Backend (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGO_URL` | MongoDB Atlas connection string | `mongodb+srv://...` |
| `DB_NAME` | Database name | `tripstars_production` |
| `JWT_SECRET` | Secret key for JWT tokens | `your-secret-key` |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry | `7` |
| `CORS_ORIGINS` | Allowed origins for CORS | `https://yourdomain.com` |
| `SMTP_HOST` | SMTP server host | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USER` | SMTP username | `email@gmail.com` |
| `SMTP_PASSWORD` | SMTP password/app password | `xxx` |
| `FROM_EMAIL` | Sender email address | `noreply@tripstars.com` |

### Frontend (.env.production)

| Variable | Description | Example |
|----------|-------------|---------|
| `REACT_APP_BACKEND_URL` | Backend API URL | `https://yourdomain.com` |

---

## Troubleshooting

### Backend Not Starting

```bash
# Check PM2 logs
pm2 logs tripstars-backend --lines 100

# Check if port is in use
sudo lsof -i :8001

# Test backend manually
cd /var/www/tripstars/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### MongoDB Connection Issues

```bash
# Test connection from server
python3 -c "
from pymongo import MongoClient
client = MongoClient('your-mongo-url')
print(client.list_database_names())
"
```

### Nginx Issues

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Reload configuration
sudo systemctl reload nginx
```

### WebSocket Not Working

1. Check Nginx WebSocket headers in config
2. Ensure `proxy_read_timeout` is high enough
3. Check browser console for connection errors

### File Upload Issues

1. Check `client_max_body_size` in Nginx config
2. Verify upload directory permissions:
```bash
ls -la /var/www/tripstars/backend/uploads/
```

---

## Quick Deploy Script

Create `deploy.sh` for quick updates:

```bash
#!/bin/bash
set -e

echo "Deploying TripStars..."

cd /var/www/tripstars

# Pull latest code
git pull origin main

# Backend
echo "Updating backend..."
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Frontend
echo "Building frontend..."
cd ../frontend
npm install
npm run build

# Restart services
echo "Restarting services..."
pm2 restart tripstars-backend

echo "Deployment complete!"
```

Make it executable:
```bash
chmod +x deploy.sh
```

---

## Security Checklist

- [ ] Change default JWT_SECRET
- [ ] Restrict MongoDB Atlas IP whitelist
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Set proper CORS_ORIGINS (not `*`)
- [ ] Keep packages updated
- [ ] Enable firewall (ufw)
- [ ] Set up log rotation
- [ ] Regular database backups

---

## Support

For issues or questions:
- Check application logs: `pm2 logs`
- Check Nginx logs: `/var/log/nginx/`
- MongoDB Atlas monitoring dashboard
