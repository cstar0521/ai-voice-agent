# Railway Deployment Setup

## Quick Deployment Steps

### 1. Push Code to GitHub

```bash
git add .
git commit -m "feat: Railway deployment setup"
git push origin main
```

### 2. Create Railway Project

1. Go to [railway.app](https://railway.app)
2. "New Project" → "Deploy from GitHub repo"
3. Select your repository → backend directory

### 3. Set Environment Variables in Railway Dashboard

Go to your Railway project → Variables tab and add:

```bash
ENVIRONMENT=production
MONGODB_URI=your_mongodb_connection_string
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
OPENAI_API_KEY=your_openai_api_key
SPEECH_PROVIDER=sarvam_ai
SARVAM_API_KEY=your_sarvam_api_key
JWT_SECRET_KEY=generate_secure_64_char_key
API_KEY=generate_secure_32_char_key
AUDIO_CACHE_ENABLED=true
CLOUD_PROVIDER=local
```

### 4. After Deployment

Get your Railway URL and add:

```bash
BASE_URL=https://your-app.railway.app
WEBHOOK_BASE_URL=https://your-app.railway.app
```

### 5. Test

Visit: `https://your-app.railway.app/health`

## Environment Variables Reference

- **MONGODB_URI**: MongoDB Atlas connection string
- **TWILIO\_\***: Twilio credentials from console
- **OPENAI_API_KEY**: OpenAI API key
- **SARVAM_API_KEY**: Sarvam AI API key
- **JWT_SECRET_KEY**: Generate with `openssl rand -base64 48`
- **API_KEY**: Generate with `openssl rand -base64 24`

## Support

- Railway Documentation: [docs.railway.app](https://docs.railway.app)
- Health Check: `/health` endpoint
- API Docs: `/docs` endpoint
