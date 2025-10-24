# Setup Guide

## Initial Setup

### 1. Install Git (if not already installed)

Download and install Git from: https://git-scm.com/download/win

After installation, initialize the repository:
```bash
git init
git add .
git commit -m "Initial commit: Project structure setup"
```

### 2. Configure Environment Variables

Copy the example environment files:
```bash
copy .env.example .env
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env
```

Edit `.env` and fill in your API credentials:
- Twilio credentials (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER)
- OpenAI API key (OPENAI_API_KEY)
- JWT secret key (JWT_SECRET_KEY) - generate a secure random string

### 3. Start with Docker Compose

Make sure Docker Desktop is installed and running, then:
```bash
docker-compose up --build
```

This will start:
- MongoDB on port 27017
- Backend API on port 8000
- Frontend dashboard on port 3000

### 4. Verify Installation

- Frontend: Open http://localhost:3000
- Backend API: Open http://localhost:8000
- API Documentation: Open http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Local Development (without Docker)

### Backend

1. Install Python 3.10+
2. Create virtual environment:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start MongoDB (via Docker or local installation)

5. Run the backend:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

1. Install Node.js 18+
2. Install dependencies:
```bash
cd frontend
npm install
```

3. Start the development server:
```bash
npm start
```

## Troubleshooting

### Port Already in Use

If ports 3000, 8000, or 27017 are already in use, you can modify the ports in `docker-compose.yml`.

### Docker Build Issues

Clear Docker cache and rebuild:
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### MongoDB Connection Issues

Ensure MongoDB is running and accessible. Check the connection string in your `.env` file.

## Next Steps

After setup is complete, refer to the [Implementation Tasks](.kiro/specs/ai-voice-loan-agent/tasks.md) to continue development.
