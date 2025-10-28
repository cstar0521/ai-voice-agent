# 🎉 Twilio Integration Setup Guide

This guide will help you set up Twilio telephony integration with ngrok for local development.

## 📋 Prerequisites

1. **Twilio Account** - Sign up at [twilio.com](https://www.twilio.com/)
2. **ngrok** - Download from [ngrok.com](https://ngrok.com/)
3. **Backend server** - Make sure your FastAPI server is running

## 🔧 Step 1: Get Twilio Credentials

### 1.1 Create Twilio Account

1. Go to [https://www.twilio.com/](https://www.twilio.com/)
2. Sign up for a free account
3. Verify your phone number

### 1.2 Get Account Credentials

1. Go to [Twilio Console](https://console.twilio.com/)
2. From the dashboard, copy:
   - **Account SID** (starts with `AC...`)
   - **Auth Token** (click the eye icon to reveal)

### 1.3 Get a Phone Number

1. In Twilio Console, go to **Phone Numbers** → **Manage** → **Buy a number**
2. Choose a number (free trial gives you one number)
3. Buy the number and copy it (format: `+1234567890`)

## 🌐 Step 2: Install and Setup ngrok

### 2.1 Install ngrok

```bash
# Download from https://ngrok.com/download
# Or using package managers:

# macOS (Homebrew)
brew install ngrok/ngrok/ngrok

# Windows (Chocolatey)
choco install ngrok

# Linux (Snap)
sudo snap install ngrok
```

### 2.2 Setup ngrok Auth Token

1. Sign up at [ngrok.com](https://ngrok.com/)
2. Get your auth token from the dashboard
3. Configure it:

```bash
ngrok authtoken YOUR_AUTH_TOKEN
```

### 2.3 Start ngrok

```bash
# Start ngrok to expose port 8000
ngrok http 8000
```

Keep this terminal open! You'll see output like:

```
Forwarding  https://abc123.ngrok.io -> http://localhost:8000
```

Copy the `https://abc123.ngrok.io` URL - this is your ngrok URL.

## ⚙️ Step 3: Configure Environment Variables

### 3.1 Create/Update backend/.env file

```bash
# Database
MONGODB_URI=mongodb://localhost:27017/voice_agent

# Twilio Configuration
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890

# Webhook URLs (replace with your ngrok URL)
WEBHOOK_BASE_URL=https://abc123.ngrok.io
BASE_URL=https://abc123.ngrok.io

# OpenAI (for NLU)
OPENAI_API_KEY=your_openai_key_here

# Speech Provider
SPEECH_PROVIDER=sarvam_ai
SARVAM_API_KEY=your_sarvam_key_here

# Security
JWT_SECRET_KEY=your-secure-jwt-secret-key
API_KEY=your-webhook-api-key

# Environment
ENVIRONMENT=development
```

### 3.2 Run the Setup Script

```bash
# This will automatically configure ngrok URLs
python setup_ngrok.py
```

## 📞 Step 4: Configure Twilio Webhooks

### 4.1 Configure Your Phone Number

1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to **Phone Numbers** → **Manage** → **Active numbers**
3. Click on your Twilio phone number
4. In the **Voice** section, set:
   - **Webhook URL**: `https://your-ngrok-url.ngrok.io/api/v1/calls/inbound/webhook`
   - **HTTP Method**: `POST`
5. In the **Status Callback** section, set:
   - **Status Callback URL**: `https://your-ngrok-url.ngrok.io/api/v1/calls/status/webhook`
   - **HTTP Method**: `POST`
6. Click **Save configuration**

### 4.2 Webhook URLs Reference

Replace `https://your-ngrok-url.ngrok.io` with your actual ngrok URL:

- **Inbound Call Webhook**: `/api/v1/calls/inbound/webhook`
- **Call Status Webhook**: `/api/v1/calls/status/webhook`
- **Recording Status Webhook**: `/api/v1/calls/recording/webhook`
- **Speech Result Webhook**: `/api/v1/calls/speech/webhook`

## 🧪 Step 5: Test the Setup

### 5.1 Run the Test Script

```bash
python test_twilio_setup.py
```

This will verify:

- ✅ Environment variables are set
- ✅ Twilio connection works
- ✅ Webhook endpoints are accessible

### 5.2 Start Your Backend Server

```bash
cd backend
python main.py
```

### 5.3 Test with a Phone Call

1. Call your Twilio phone number
2. You should hear: "Hello! Thank you for calling. How can I help you with your education loan today?"
3. Check your backend logs for webhook calls

### 5.4 Test Outbound Calls (via API)

```bash
curl -X POST "http://localhost:8000/api/v1/calls/outbound" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "phone_number": "+1234567890",
    "language": "hinglish"
  }'
```

## 🔍 Troubleshooting

### Common Issues

#### 1. "Twilio client not initialized"

- Check your `.env` file has correct Twilio credentials
- Verify credentials in Twilio Console

#### 2. "Webhook signature validation failed"

- Make sure ngrok URL is correct in Twilio configuration
- Check that `WEBHOOK_BASE_URL` matches your ngrok URL

#### 3. "Server not running" for webhook endpoints

- Make sure your FastAPI server is running on port 8000
- Verify ngrok is forwarding to the correct port

#### 4. Calls not connecting

- Check Twilio account balance (free trial has limitations)
- Verify phone number format (E.164: +1234567890)
- Check Twilio debugger: https://console.twilio.com/us1/develop/voice/manage/debugger

### Debug Steps

1. **Check ngrok status**:

   ```bash
   curl http://localhost:4040/api/tunnels
   ```

2. **Check webhook logs**:
   - Look at your backend server logs
   - Check Twilio debugger for webhook errors

3. **Test webhook manually**:
   ```bash
   curl -X POST "https://your-ngrok-url.ngrok.io/api/v1/calls/inbound/webhook" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "CallSid=test&From=+1234567890&CallStatus=ringing"
   ```

## 🚀 Production Deployment

When deploying to production:

1. **Replace ngrok URL** with your production domain
2. **Update Twilio webhooks** to point to production URLs
3. **Set production environment variables**
4. **Enable webhook signature validation** in production

Example production URLs:

- `https://api.yourdomain.com/api/v1/calls/inbound/webhook`
- `https://api.yourdomain.com/api/v1/calls/status/webhook`

## 📚 Additional Resources

- [Twilio Voice API Documentation](https://www.twilio.com/docs/voice)
- [Twilio Webhooks Guide](https://www.twilio.com/docs/usage/webhooks)
- [ngrok Documentation](https://ngrok.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 🎯 What's Already Implemented

The following Twilio features are already implemented in the codebase:

✅ **Call Management**:

- Outbound call initiation
- Inbound call handling
- Call status tracking
- Call hangup

✅ **Recording**:

- Start/stop recording
- Recording status callbacks
- Recording URL storage

✅ **Speech Processing**:

- Speech-to-text integration
- Real-time speech recognition
- Multi-language support

✅ **Webhooks**:

- Signature validation
- Status callbacks
- Recording callbacks
- Speech result callbacks

✅ **Security**:

- Webhook signature validation
- API key authentication
- JWT token authentication

You're all set! 🎉
