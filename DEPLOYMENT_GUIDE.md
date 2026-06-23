# Medical AI Engine - Deployment Guide

Complete guide for deploying Medical AI Engine to production.

---

## 🚀 Deployment Options

### 1. Railway (Recommended - Easiest)
### 2. Heroku
### 3. AWS EC2
### 4. Docker (Self-hosted)

---

## Option 1: Railway Deployment (Recommended)

### Prerequisites
- Railway account (https://railway.app)
- GitHub repository with Medical AI Engine code
- DeepSeek API key

### Steps

#### 1. Create Railway Project
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login to Railway
railway login

# Create new project
railway init
```

#### 2. Connect GitHub Repository
1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub"
4. Connect your GitHub account
5. Select medical-ai-engine repository

#### 3. Configure Environment Variables
In Railway Dashboard:
1. Go to Variables tab
2. Add the following:
   ```
   DEEPSEEK_API_KEY=your_deepseek_key_here
   DATABASE_URL=sqlite:///./medical_questions.db
   LOG_LEVEL=INFO
   ENVIRONMENT=production
   CORS_ORIGINS=*
   ```

#### 4. Deploy
```bash
# Deploy from CLI
railway up

# Or push to GitHub and Railway auto-deploys
git push origin main
```

#### 5. Get Production URL
- Railway provides a public URL like: `https://medical-ai-engine-prod.railway.app`
- Use this URL in OKSmed app settings

---

## Option 2: Heroku Deployment

### Prerequisites
- Heroku account (https://heroku.com)
- Heroku CLI installed
- DeepSeek API key

### Steps

#### 1. Create Heroku App
```bash
# Login to Heroku
heroku login

# Create app
heroku create medical-ai-engine-prod

# Add buildpack for Python
heroku buildpacks:add heroku/python
```

#### 2. Set Environment Variables
```bash
heroku config:set DEEPSEEK_API_KEY=your_key_here
heroku config:set DATABASE_URL=sqlite:///./medical_questions.db
heroku config:set LOG_LEVEL=INFO
heroku config:set ENVIRONMENT=production
```

#### 3. Deploy
```bash
# Push to Heroku
git push heroku main

# View logs
heroku logs --tail
```

#### 4. Get Production URL
- Heroku provides: `https://medical-ai-engine-prod.herokuapp.com`

---

## Option 3: AWS EC2 Deployment

### Prerequisites
- AWS account
- EC2 instance (t3.small or larger)
- Ubuntu 22.04 LTS
- Domain name (optional)

### Steps

#### 1. Launch EC2 Instance
```bash
# SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker ubuntu
```

#### 2. Clone Repository
```bash
cd /home/ubuntu
git clone https://github.com/your-repo/medical-ai-engine.git
cd medical-ai-engine
```

#### 3. Create Environment File
```bash
cat > .env << EOF
DEEPSEEK_API_KEY=your_key_here
DATABASE_URL=sqlite:///./medical_questions.db
LOG_LEVEL=INFO
ENVIRONMENT=production
CORS_ORIGINS=*
EOF
```

#### 4. Build and Run with Docker
```bash
# Build image
docker build -t medical-ai-engine:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  -v /home/ubuntu/medical-ai-engine/data:/app/data \
  --name medical-ai-engine \
  --restart unless-stopped \
  medical-ai-engine:latest

# Verify running
docker ps
```

#### 5. Setup Nginx Reverse Proxy
```bash
# Install Nginx
sudo apt install nginx -y

# Create config
sudo tee /etc/nginx/sites-available/medical-ai-engine > /dev/null << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/medical-ai-engine /etc/nginx/sites-enabled/

# Test and restart
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. Setup SSL with Let's Encrypt
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

---

## Option 4: Docker (Self-hosted)

### Prerequisites
- Docker and Docker Compose installed
- Linux/Mac/Windows with Docker

### Steps

#### 1. Prepare Environment
```bash
cd medical-ai-engine
cp .env.example .env

# Edit .env with your settings
nano .env
```

#### 2. Build and Run
```bash
# Build image
docker build -t medical-ai-engine:latest .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f
```

#### 3. Access API
- Local: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

---

## 🔗 Integration with OKSmed App

### 1. Update API Endpoint

Edit `app/settings-api.tsx` in OKSmed:

```typescript
const DEFAULT_API_URL = 'https://medical-ai-engine-prod.railway.app';
// or
const DEFAULT_API_URL = 'https://medical-ai-engine-prod.herokuapp.com';
// or
const DEFAULT_API_URL = 'https://your-domain.com';
```

### 2. Test Connection

In OKSmed Settings:
1. Go to Settings tab
2. Enter production API URL
3. Tap "Test Connection"
4. Should see "✓ Connected" message

### 3. Update Environment Variables

Create `.env` in OKSmed root:
```
EXPO_PUBLIC_MEDICAL_AI_API_URL=https://your-production-url.com
```

---

## 📊 Monitoring & Maintenance

### Health Checks
```bash
# Check API health
curl https://your-api-url.com/health

# Response should be:
# {"status": "healthy", "version": "1.0.0"}
```

### View Logs

#### Railway
```bash
railway logs
```

#### Heroku
```bash
heroku logs --tail
```

#### Docker
```bash
docker-compose logs -f medical-ai-engine
```

### Database Backup
```bash
# Backup SQLite database
cp medical_questions.db medical_questions.db.backup

# Or setup automated backups
# For production, consider migrating to PostgreSQL
```

---

## 🔒 Security Best Practices

### 1. Environment Variables
- Never commit `.env` files
- Use platform-specific secret management
- Rotate API keys regularly

### 2. CORS Configuration
```python
# In production, set specific origins
CORS_ORIGINS = "https://your-app-domain.com"
```

### 3. Rate Limiting
```python
# Add rate limiting to prevent abuse
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/extract/pdf")
@limiter.limit("10/minute")
async def extract_pdf(file: UploadFile):
    ...
```

### 4. API Authentication (Optional)
```python
# Add API key authentication
API_KEY_HEADER = "X-API-Key"

@app.post("/extract/pdf")
async def extract_pdf(
    file: UploadFile,
    x_api_key: str = Header(None)
):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    ...
```

---

## 🐛 Troubleshooting

### Issue: "Connection refused"
**Solution:**
- Check if server is running: `docker ps`
- Verify firewall rules
- Check security groups (AWS)
- Ensure port 8000 is exposed

### Issue: "API key not working"
**Solution:**
- Verify DeepSeek API key is correct
- Check if key has sufficient quota
- Ensure key is in `.env` file
- Restart container after updating

### Issue: "Out of memory"
**Solution:**
- Increase container memory: `docker run -m 2g`
- Optimize PDF processing
- Implement caching
- Use PostgreSQL instead of SQLite

### Issue: "Slow response times"
**Solution:**
- Add caching layer (Redis)
- Optimize OCR settings
- Use CDN for static files
- Scale horizontally (multiple instances)

---

## 📈 Performance Optimization

### 1. Caching
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_question(question_id: int):
    ...
```

### 2. Database Optimization
```python
# Use PostgreSQL for production
DATABASE_URL = "postgresql://user:password@host/dbname"

# Add indexes
CREATE INDEX idx_subject ON questions(subject);
CREATE INDEX idx_lesson ON questions(lesson);
```

### 3. Load Balancing
```yaml
# docker-compose.yml with multiple instances
services:
  api-1:
    image: medical-ai-engine:latest
    ports:
      - "8001:8000"
  api-2:
    image: medical-ai-engine:latest
    ports:
      - "8002:8000"
  nginx:
    # Load balance between api-1 and api-2
```

---

## 📝 Deployment Checklist

- [ ] DeepSeek API key obtained
- [ ] Environment variables configured
- [ ] Database initialized
- [ ] CORS origins configured
- [ ] SSL certificate installed (if using custom domain)
- [ ] Health checks passing
- [ ] API documentation accessible
- [ ] OKSmed app updated with production URL
- [ ] End-to-end testing completed
- [ ] Monitoring and logging setup
- [ ] Backup strategy implemented
- [ ] Documentation updated

---

## 🆘 Support

For deployment issues:
1. Check logs: `docker-compose logs -f`
2. Verify environment variables
3. Test API directly: `curl https://your-api-url.com/health`
4. Check DeepSeek API status
5. Review firewall/security group rules

---

**Deployment Ready!** 🚀

Your Medical AI Engine is ready for production!
