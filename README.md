# AI Voice Loan Agent

A multilingual voice-based system that qualifies students and working professionals exploring study-abroad education loans. The system handles both inbound and outbound calls, collects eligibility data, answers FAQs, and transfers qualified leads to human loan experts.

## Features

- Multilingual support (Hinglish, English, Telugu)
- Automated call handling (inbound and outbound)
- Real-time sentiment analysis
- Intelligent lead qualification
- Human expert handoff
- CRM integration
- Analytics dashboard

## Project Structure

```
.
├── backend/          # Python FastAPI backend
├── frontend/         # React dashboard
├── shared/           # Shared types and utilities
├── docker-compose.yml
└── README.md
```

## Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.10+ (for local backend development)

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-voice-loan-agent
```

2. Copy environment variables:
```bash
cp .env.example .env
```

3. Fill in your API keys and credentials in `.env`

4. Start the services:
```bash
docker-compose up
```

5. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - MongoDB: localhost:27017

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

## Environment Variables

See `.env.example` for required environment variables.

Key variables:
- `MONGODB_URI` - MongoDB connection string
- `TWILIO_ACCOUNT_SID` - Twilio account SID
- `TWILIO_AUTH_TOKEN` - Twilio auth token
- `OPENAI_API_KEY` - OpenAI API key
- `JWT_SECRET_KEY` - Secret key for JWT tokens

## Documentation

- [Requirements](.kiro/specs/ai-voice-loan-agent/requirements.md)
- [Design](.kiro/specs/ai-voice-loan-agent/design.md)
- [Implementation Tasks](.kiro/specs/ai-voice-loan-agent/tasks.md)

## License

Proprietary
