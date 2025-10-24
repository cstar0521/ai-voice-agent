# Project Structure

```
ai-voice-loan-agent/
├── backend/                      # Python FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models/              # Pydantic data models
│   │   │   └── __init__.py
│   │   ├── services/            # Business logic
│   │   │   └── __init__.py
│   │   ├── repositories/        # Database access layer
│   │   │   └── __init__.py
│   │   ├── api/                 # API route handlers
│   │   │   └── __init__.py
│   │   └── integrations/        # External service adapters
│   │       └── __init__.py
│   ├── tests/                   # Backend tests
│   │   └── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Configuration management
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile              # Backend Docker configuration
│   └── .env.example            # Backend environment variables template
│
├── frontend/                    # React dashboard
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/         # Reusable React components
│   │   ├── pages/              # Page components
│   │   ├── services/           # API client services
│   │   ├── utils/              # Utility functions
│   │   ├── App.js              # Main App component
│   │   └── index.js            # React entry point
│   ├── package.json            # Node.js dependencies
│   ├── Dockerfile              # Frontend Docker configuration
│   └── .env.example            # Frontend environment variables template
│
├── shared/                      # Shared code between frontend and backend
│   └── README.md
│
├── .kiro/                       # Kiro spec files
│   └── specs/
│       └── ai-voice-loan-agent/
│           ├── requirements.md
│           ├── design.md
│           └── tasks.md
│
├── docker-compose.yml          # Docker Compose configuration
├── .env.example                # Root environment variables template
├── .gitignore                  # Git ignore rules
├── README.md                   # Project overview
├── SETUP.md                    # Setup instructions
└── PROJECT_STRUCTURE.md        # This file

```

## Directory Descriptions

### Backend (`/backend`)

- **app/models/** - Pydantic models for Lead, Call, Conversation, etc.
- **app/services/** - Business logic (NLU, sentiment analysis, eligibility engine, conversation manager)
- **app/repositories/** - Database access patterns (LeadRepository, CallRepository, etc.)
- **app/api/** - FastAPI route handlers organized by resource
- **app/integrations/** - Adapters for Twilio, Google Cloud/AWS, notifications, CRM
- **tests/** - Unit and integration tests
- **main.py** - FastAPI app initialization with middleware
- **config.py** - Centralized configuration using Pydantic Settings

### Frontend (`/frontend`)

- **src/components/** - Reusable UI components (CallCard, LeadTable, MetricsCard, etc.)
- **src/pages/** - Page-level components (Dashboard, LeadManagement, Analytics, Config)
- **src/services/** - API client for backend communication
- **src/utils/** - Helper functions and utilities
- **App.js** - Main application with routing and theme

### Shared (`/shared`)

- Common types, constants, and utilities used by both frontend and backend
- Will be populated as needed during development

## Key Files

- **docker-compose.yml** - Orchestrates MongoDB, backend, and frontend services
- **.env.example** - Template for environment variables (copy to .env)
- **README.md** - Project overview and quick start guide
- **SETUP.md** - Detailed setup instructions

## Development Workflow

1. Start services: `docker-compose up`
2. Backend API: http://localhost:8000
3. Frontend: http://localhost:3000
4. MongoDB: localhost:27017

## Next Steps

Refer to `.kiro/specs/ai-voice-loan-agent/tasks.md` for the implementation roadmap.
