# Deployment Guide for Road Rage Detection App

## ⚠️ Important Note About Railway

Railway requires you to create a project first. If you see "No service linked", follow these steps:

```bash
# 1. Login (opens browser)
railway login

# 2. Create new project
railway init

# 3. Now you can set variables
railway variables set GEMINI_API_KEY=your_key_here

# 4. Deploy
railway up
```

However, **Railway may not be ideal** for this app due to:
- Video processing needs (ffmpeg)
- Large file uploads (500MB)
- High memory requirements
- Limited free tier resources

---

## 🚀 Recommended Deployment Options

### Option 1: Docker (Local or Any Server) - EASIEST

Perfect for testing or deploying to any server with Docker installed.

**Prerequisites:**
- Docker installed
- Docker Compose installed

**Steps:**
```bash
# 1. Make sure you have a .env file with your API key
echo "GEMINI_API_KEY=your_key_here" > .env

# 2. Build and run with Docker Compose
docker-compose up -d

# 3. Access at http://localhost:5000

# 4. View logs
docker-compose logs -f

# 5. Stop
docker-compose down
```

**To deploy on a remote server:**
```bash
# Copy files to server
scp -r . user@your-server:/path/to/app

# SSH into server
ssh user@your-server

# Navigate to app directory
cd /path/to/app

# Run docker-compose
docker-compose up -d
```

---

### Option 2: Render.com - RECOMMENDED FOR CLOUD

Render has a good free tier and supports ffmpeg out of the box.

**Steps:**

1. **Push code to GitHub:**
   ```bash
   git add .
   git commit -m "Add deployment files"
   git push origin master
   ```

2. **Create account at [render.com](https://render.com)**

3. **Create New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select `road_rage_poc` repository

4. **Configure Service:**
   - **Name:** road-rage-detection
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 600`
   - **Plan:** Free (or paid for better performance)

5. **Add Environment Variables:**
   - Go to "Environment" tab
   - Add: `GEMINI_API_KEY` = your_api_key_here

6. **Deploy:**
   - Click "Create Web Service"
   - Wait for build and deployment
   - Access your app at the provided URL

**Limitations on Free Tier:**
- Sleeps after 15 minutes of inactivity
- 512MB RAM (may struggle with large videos)
- Limited bandwidth

---

### Option 3: VPS (DigitalOcean, AWS, Linode) - BEST FOR PRODUCTION

For serious production use with large videos and multiple users.

**Prerequisites:**
- VPS with Ubuntu 22.04 (recommended: 4GB RAM, 2 CPUs)
- Domain name (optional but recommended)

**Complete Setup:**

```bash
# 1. SSH into your server
ssh root@your-server-ip

# 2. Update system
apt update && apt upgrade -y

# 3. Install dependencies
apt install -y python3-pip python3-venv nginx ffmpeg git

# 4. Create app user (optional but recommended)
adduser roadrage
usermod -aG sudo roadrage
su - roadrage

# 5. Clone/upload your code
git clone https://github.com/yourusername/road_rage_poc.git
cd road_rage_poc

# or upload with scp:
# scp -r /local/path/to/road_rage_poc user@server:/home/user/

# 6. Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 7. Create .env file
nano .env
# Add: GEMINI_API_KEY=your_key_here
# Save: Ctrl+X, Y, Enter

# 8. Test the app
python app.py
# Access at http://your-server-ip:5000
# Press Ctrl+C to stop

# 9. Create systemd service
sudo nano /etc/systemd/system/roadrage.service
```

**Paste this into the service file:**
```ini
[Unit]
Description=Road Rage Detection Web Application
After=network.target

[Service]
User=roadrage
WorkingDirectory=/home/roadrage/road_rage_poc
Environment="PATH=/home/roadrage/road_rage_poc/venv/bin"
EnvironmentFile=/home/roadrage/road_rage_poc/.env
ExecStart=/home/roadrage/road_rage_poc/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 --timeout 600 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Continue setup:**
```bash
# 10. Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable roadrage
sudo systemctl start roadrage
sudo systemctl status roadrage

# 11. Configure Nginx
sudo nano /etc/nginx/sites-available/roadrage
```

**Paste this Nginx configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;  # or use server IP
    
    client_max_body_size 500M;
    client_body_timeout 600s;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE support for real-time updates
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        
        # Timeouts for long video processing
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}
```

**Enable Nginx:**
```bash
# 12. Enable site and restart Nginx
sudo ln -s /etc/nginx/sites-available/roadrage /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 13. Configure firewall
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS (for future SSL)
sudo ufw enable

# 14. (Optional) Set up SSL with Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

**Your app is now live!**
- Access at: http://your-domain.com (or http://your-server-ip)

**Useful commands:**
```bash
# View logs
sudo journalctl -u roadrage -f

# Restart service
sudo systemctl restart roadrage

# Check status
sudo systemctl status roadrage

# Pull latest code
cd /home/roadrage/road_rage_poc
git pull
sudo systemctl restart roadrage
```

---

### Option 4: Railway (After Fixing Your Issue)

Since you already have Railway CLI installed:

```bash
# 1. Login
railway login

# 2. Initialize project (this was missing!)
railway init
# Choose: "Create new project"
# Name it: "road-rage-detection"

# 3. Add environment variable
railway variables set GEMINI_API_KEY=AIzaSyAHrmFcZDH9AznlPHzjuoBvKulR7NdM4Go

# 4. Deploy
railway up

# 5. Check status
railway status

# 6. View logs
railway logs
```

**Note:** Railway automatically detects the Procfile and will use it.

---

## 🔧 Production Checklist

Before deploying to production, update `app.py`:

### 1. Remove Debug Mode

Find line 444 and change:
```python
# From:
app.run(debug=True, threaded=True, host='0.0.0.0', port=5000)

# To:
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
```

### 2. Add HTTPS Support

Use your deployment platform's SSL certificate or Let's Encrypt.

### 3. Add Authentication

Add user login to prevent unauthorized access.

### 4. Set Up Monitoring

- Application monitoring: Sentry, DataDog
- Server monitoring: Uptime Robot, Pingdom
- Log aggregation: Papertrail, Loggly

### 5. Implement Rate Limiting

Add Flask-Limiter to prevent abuse:
```bash
pip install Flask-Limiter
```

### 6. Add Job Cleanup

Videos and results can fill up disk space. Add automatic cleanup for old jobs.

---

## 📊 Resource Requirements

### Minimum (Small videos, 1-2 users):
- 2GB RAM
- 1 CPU core
- 20GB storage

### Recommended (Production, multiple users):
- 4GB+ RAM
- 2+ CPU cores
- 50GB+ storage
- Consider S3/cloud storage for videos

---

## 🆘 Troubleshooting

### "No service linked" on Railway
- Run `railway init` first to create a project

### "Module not found" errors
- Make sure all requirements are in `requirements.txt`
- Run: `pip install -r requirements.txt`

### ffmpeg not found
- Docker: Already included in Dockerfile
- VPS: `sudo apt install ffmpeg`
- macOS: `brew install ffmpeg`

### Out of memory errors
- Increase worker count in gunicorn
- Use smaller videos for testing
- Upgrade to larger server instance

### Videos not uploading
- Check `client_max_body_size` in Nginx config
- Check disk space: `df -h`
- Check upload folder permissions

---

## 🎯 Quick Recommendation

**For your use case, I recommend:**

1. **Testing/Demo:** Docker locally or Docker on a small VPS
2. **Public Demo:** Render.com (easy, free tier available)
3. **Production:** VPS with Nginx + Gunicorn (full control, best performance)

Choose based on your needs and budget!
