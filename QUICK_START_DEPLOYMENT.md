# Medical AI Engine - Quick Start Deployment

Deploy Medical AI Engine in 5 minutes using Railway (recommended).

---

## 🚀 Railway Deployment (Easiest - 5 minutes)

### Step 1: Prepare Repository
```bash
cd medical-ai-engine

# Ensure .env.example exists
ls -la .env.example

# Ensure Dockerfile exists
ls -la Dockerfile
```

### Step 2: Create Railway Account
1. Go to https://railway.app
2. Sign up with GitHub
3. Authorize Railway

### Step 3: Deploy
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Deploy
railway up
```

### Step 4: Configure Environment
1. Go to Railway Dashboard
2. Select your project
3. Click "Variables" tab
4. Add:
   ```
   DEEPSEEK_API_KEY=your_key_here
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   ```

### Step 5: Get URL
1. Go to "Deployments" tab
2. Copy the public URL (e.g., `https://medical-ai-engine-prod.railway.app`)
3. Use this in OKSmed app settings

**Done!** ✅

---

## 🐳 Docker Deployment (Local Testing)

### Step 1: Build Image
```bash
docker build -t medical-ai-engine:latest .
```

### Step 2: Run Container
```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name medical-ai-engine \
  medical-ai-engine:latest
```

### Step 3: Test
```bash
curl http://localhost:8000/health
```

### Step 4: Access
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

---

## 🔗 Connect to OKSmed App

### In OKSmed Settings:
1. Go to **Settings** tab
2. Tap **API Configuration**
3. Enter your production URL:
   ```
   https://medical-ai-engine-prod.railway.app
   ```
4. Tap **Test Connection**
5. Should show ✓ Connected

### Or Update Environment:
Create `.env` in OKSmed root:
```
EXPO_PUBLIC_MEDICAL_AI_API_URL=https://your-production-url.com
```

---

## ✅ Verification Checklist

- [ ] Medical AI Engine deployed
- [ ] Health check passing
- [ ] DeepSeek API key configured
- [ ] OKSmed app updated with API URL
- [ ] Connection test successful
- [ ] Can extract questions from text
- [ ] Can extract questions from PDF
- [ ] Can extract questions from image

---

## 🆘 Quick Troubleshooting

### "Connection refused"
```bash
# Check if Railway deployment is running
railway logs

# Check health endpoint
curl https://your-api-url.com/health
```

### "API key not working"
```bash
# Verify key in Railway variables
railway variables

# Update key
railway variables DEEPSEEK_API_KEY=new_key
```

### "Timeout errors"
```bash
# Check Railway logs
railway logs --tail

# Restart deployment
railway redeploy
```

---

## 📊 Next Steps

1. **Extract Questions**: Use OKSmed to extract medical questions
2. **Monitor**: Check Railway logs for issues
3. **Scale**: Add more resources if needed
4. **Backup**: Setup automated database backups
5. **Analytics**: Add monitoring and metrics

---

**Deployment Complete!** 🎉

Your Medical AI Engine is live and connected to OKSmed!
