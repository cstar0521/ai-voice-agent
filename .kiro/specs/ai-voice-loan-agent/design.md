# Design Document

## Overview

The AI Voice Loan Agent is a microservices-based system that orchestrates voice calls with students seeking education loans. The architecture consists of a React frontend for monitoring and configuration, a Python backend handling business logic and orchestration, MongoDB for data persistence, and integration with third-party services for telephony (Twilio/Bolna), speech processing (Google Cloud/AWS), and notifications (SuprSend/Gupshup).

The system follows an event-driven architecture where call events trigger state transitions in a conversation state machine, with real-time sentiment analysis and dynamic language switching capabilities.

## Architecture

### High-Level Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  React Frontend │◄────────┤  Python Backend  │────────►│    MongoDB      │
│  (Monitoring)   │  REST   │  (FastAPI/Flask) │  CRUD   │  (Lead Data)    │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐  ┌─────▼─────┐  ┌──────▼──────┐
            │   Twilio/    │  │  Google   │  │  SuprSend/  │
            │   Bolna      │  │  Cloud/   │  │  Gupshup    │
            │  (Telephony) │  │  AWS      │  │ (WhatsApp/  │
            │              │  │  (ASR/TTS)│  │  SMS)       │
            └──────────────┘  └───────────┘  └─────────────┘
```

### Component Architecture

**Frontend Layer (React)**
- Dashboard for monitoring active calls
- Lead management interface
- Configuration panel for voice scripts and flows
- Analytics and metrics visualization

**Backend Layer (Python)**
- API Gateway (FastAPI) - RESTful endpoints for frontend and webhooks
- Call Orchestrator - Manages call lifecycle and state machine
- Conversation Manager - Handles dialogue flow and context
- NLU Engine - Intent detection and entity extraction
- Sentiment Analyzer - Real-time emotion detection
- Eligibility Engine - Rule-based loan category mapping
- Integration Layer - Adapters for external services

**Data Layer (MongoDB)**
- Leads collection - Structured lead data
- Calls collection - Call metadata and transcripts
- Conversations collection - Turn-by-turn dialogue history
- Configuration collection - Voice scripts, prompts, and rules

### Technology Stack

- **Frontend**: React 18+, Material-UI, Axios, Socket.io-client (for real-time updates)
- **Backend**: Python 3.10+, FastAPI, Pydantic, Motor (async MongoDB driver)
- **Database**: MongoDB 6.0+
- **Speech**: Sarvam AI (primary for Indian languages), Google Cloud Speech-to-Text, Google Cloud Text-to-Speech (fallback/alternative)
- **Telephony**: Twilio Voice API or Bolna
- **Notifications**: SuprSend or Gupshup API
- **NLU**: OpenAI GPT-4 API (for intent/entity extraction) or Rasa
- **Sentiment**: TextBlob + custom rules or OpenAI API
- **Deployment**: Docker, Docker Compose (development), Kubernetes (production)

## Components and Interfaces

### 1. API Gateway (FastAPI)

**Responsibilities:**
- Expose REST endpoints for frontend
- Handle webhooks from Twilio/Bolna
- Authenticate and authorize requests
- Route requests to appropriate services

**Key Endpoints:**

```python
# Call Management
POST   /api/v1/calls/outbound          # Initiate outbound call
POST   /api/v1/calls/inbound/webhook   # Twilio inbound webhook
POST   /api/v1/calls/{call_id}/hangup  # End call
GET    /api/v1/calls/{call_id}         # Get call details
GET    /api/v1/calls                   # List calls with filters

# Lead Management
GET    /api/v1/leads                   # List leads
GET    /api/v1/leads/{lead_id}         # Get lead details
PUT    /api/v1/leads/{lead_id}         # Update lead
POST   /api/v1/leads/{lead_id}/handoff # Trigger human handoff

# Configuration
GET    /api/v1/config/prompts          # Get voice prompts
PUT    /api/v1/config/prompts          # Update prompts
GET    /api/v1/config/flows            # Get conversation flows

# Analytics
GET    /api/v1/analytics/metrics       # Get KPI metrics
GET    /api/v1/analytics/calls         # Call analytics
```

**Interface Contracts:**

```python
# Request: Initiate Outbound Call
{
  "phone_number": "+919876543210",
  "lead_source": "facebook_ad",
  "preferred_language": "hinglish",
  "metadata": {
    "campaign_id": "summer_2025"
  }
}

# Response: Call Created
{
  "call_id": "call_abc123",
  "status": "initiated",
  "created_at": "2025-10-24T10:30:00Z"
}
```

### 2. Call Orchestrator

**Responsibilities:**
- Manage call lifecycle (initiated → connected → in_progress → completed/failed)
- Coordinate between telephony, ASR, TTS, and conversation manager
- Handle call events (connected, speech detected, silence, hangup)
- Implement retry logic for failed calls

**State Machine:**

```
initiated → dialing → connected → greeting → language_detection 
  → qualification → eligibility_mapping → handoff_offer 
  → [handoff_accepted → transferring → transferred]
  → [handoff_declined → followup_scheduled]
  → ending → completed

Error states: failed, no_answer, busy, network_error
```

**Key Methods:**

```python
class CallOrchestrator:
    async def initiate_outbound_call(phone: str, lead_data: dict) -> str
    async def handle_inbound_call(call_sid: str, from_number: str) -> None
    async def process_call_event(call_id: str, event: CallEvent) -> None
    async def transition_state(call_id: str, new_state: str) -> None
    async def retry_failed_call(call_id: str, attempt: int) -> None
    async def end_call(call_id: str, reason: str) -> None
```

### 3. Conversation Manager

**Responsibilities:**
- Execute conversation state machine
- Maintain conversation context (last 3 minutes)
- Generate appropriate prompts based on state and language
- Handle user responses and extract information
- Detect when to escalate or handoff

**Conversation Context:**

```python
class ConversationContext:
    call_id: str
    lead_id: str
    current_state: str
    language: str  # hinglish, english, telugu
    collected_data: dict  # degree, country, loan_amount, etc.
    turn_history: list[Turn]  # last N turns
    sentiment_history: list[float]
    negative_turn_count: int
    clarification_count: int
    last_activity: datetime
```

**Key Methods:**

```python
class ConversationManager:
    async def process_user_utterance(call_id: str, transcript: str) -> Response
    async def generate_prompt(call_id: str, state: str) -> str
    async def extract_entities(transcript: str, expected_entity: str) -> dict
    async def validate_response(response: str, expected_type: str) -> bool
    async def switch_language(call_id: str, new_language: str) -> None
    async def should_escalate(call_id: str) -> bool
```

### 4. NLU Engine

**Responsibilities:**
- Detect user intent from transcript
- Extract entities (country, degree, loan_amount, etc.)
- Calculate confidence scores
- Handle multilingual input (Hinglish, English, Telugu)

**Intents:**

```python
class Intent(Enum):
    LOAN_INTEREST = "loan_interest"
    HAS_OFFER = "has_offer"
    NO_OFFER = "no_offer"
    COAPPLICANT_YES = "coapplicant_yes"
    COAPPLICANT_NO = "coapplicant_no"
    COLLATERAL_YES = "collateral_yes"
    COLLATERAL_NO = "collateral_no"
    VISA_TIMELINE = "visa_timeline"
    HANDOFF_REQUEST = "handoff_request"
    FAQ = "faq"
    LANGUAGE_SWITCH = "language_switch"
    GOODBYE = "goodbye"
    UNCLEAR = "unclear"
```

**Entity Types:**

```python
class EntityType(Enum):
    COUNTRY = "country"  # US, UK, Canada, Australia, Germany, etc.
    DEGREE = "degree"  # bachelors, masters, mba
    LOAN_AMOUNT = "loan_amount"  # numeric value
    COLLATERAL = "collateral"  # yes/no
    ITR = "itr"  # yes/no
    VISA_DATE = "visa_date"  # date or relative time
    URGENCY = "urgency"  # high, medium, low
    LANGUAGE = "language"  # hinglish, english, telugu
```

**Implementation Approach:**

```python
class NLUEngine:
    async def detect_intent(transcript: str, language: str) -> Intent
    async def extract_entities(transcript: str, context: dict) -> dict
    async def get_confidence_score(transcript: str, intent: Intent) -> float
    
    # Use OpenAI GPT-4 with structured prompts
    # Fallback to regex patterns for simple entities
    # Language-specific entity extraction rules
```

### 5. Sentiment Analyzer

**Responsibilities:**
- Analyze user sentiment in real-time
- Track sentiment trends across conversation
- Trigger escalation when negative sentiment detected
- Support multilingual sentiment analysis

**Sentiment Scoring:**

```python
class SentimentAnalyzer:
    async def analyze_sentiment(transcript: str, language: str) -> float
    # Returns score: -1.0 (very negative) to +1.0 (very positive)
    
    async def is_negative_sentiment(score: float) -> bool
    # Returns True if score < -0.3
    
    async def detect_frustration_keywords(transcript: str, language: str) -> bool
    # Checks for keywords like "not clear", "confused", "want person"
```

**Implementation:**
- Use TextBlob for English sentiment
- Use OpenAI API for Hinglish/Telugu sentiment
- Maintain rule-based keyword detection for common frustration phrases
- Combine scores: 70% ML model + 30% keyword rules

### 6. Eligibility Engine

**Responsibilities:**
- Map collected data to loan categories
- Apply business rules for eligibility
- Determine urgency level
- Generate lender recommendations

**Eligibility Rules:**

```python
class EligibilityEngine:
    def determine_category(lead_data: dict) -> str:
        """
        Returns: public_secured, private_unsecured, intl_usd, or escalate
        """
        if lead_data["collateral"] == "yes":
            return "public_secured"
        
        if lead_data["collateral"] == "no" and lead_data["coapplicant_itr"] == "yes":
            return "private_unsecured"
        
        if lead_data["country"] in ["US", "Canada"] and lead_data.get("high_merit"):
            return "intl_usd"
        
        if lead_data["collateral"] == "no" and lead_data["coapplicant_itr"] == "no":
            return "escalate"
        
        return "escalate"
    
    def determine_urgency(visa_timeline: str) -> str:
        """
        Returns: high, medium, low
        """
        # Parse visa_timeline and calculate days
        # < 30 days = high
        # 30-90 days = medium
        # > 90 days = low
    
    def get_lender_recommendations(category: str, urgency: str) -> list[str]:
        """
        Returns list of recommended lenders
        """
```

### 7. Integration Layer

**Telephony Adapter (Twilio/Bolna):**

```python
class TelephonyAdapter:
    async def make_call(to_number: str, callback_url: str) -> str
    async def answer_call(call_sid: str) -> None
    async def transfer_call(call_sid: str, to_number: str) -> None
    async def hangup_call(call_sid: str) -> None
    async def play_audio(call_sid: str, audio_url: str) -> None
    async def start_recording(call_sid: str) -> None
    async def stop_recording(call_sid: str) -> None
```

**Speech Adapter (Sarvam AI / Google Cloud / AWS):**

```python
class SpeechAdapter:
    async def transcribe_audio(audio_stream: bytes, language: str) -> str
    async def synthesize_speech(text: str, language: str, voice: str) -> bytes
    async def detect_language(audio_stream: bytes) -> str
    
class SarvamSpeechAdapter(SpeechAdapter):
    """Sarvam AI implementation for Indian languages (Hinglish, Hindi, Telugu)"""
    async def transcribe_audio(audio_stream: bytes, language: str) -> str
    async def synthesize_speech(text: str, language: str, voice: str) -> bytes
    async def translate_text(text: str, source_lang: str, target_lang: str) -> str
```

**Notification Adapter (SuprSend/Gupshup):**

```python
class NotificationAdapter:
    async def send_whatsapp(phone: str, message: str, template_id: str) -> bool
    async def send_sms(phone: str, message: str) -> bool
```

**CRM Adapter:**

```python
class CRMAdapter:
    async def create_lead(lead_data: dict) -> str
    async def update_lead(lead_id: str, updates: dict) -> bool
    async def get_lead(lead_id: str) -> dict
    async def notify_expert(lead_id: str, expert_id: str) -> bool
```

## Data Models

### Lead Model

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Lead(BaseModel):
    lead_id: str = Field(default_factory=lambda: f"lead_{uuid.uuid4().hex[:12]}")
    name: Optional[str] = None
    phone: str
    language: str  # hinglish, english, telugu
    country: Optional[str] = None
    degree: Optional[str] = None  # bachelors, masters, mba
    loan_amount: Optional[float] = None
    offer_letter: Optional[str] = None  # yes, no
    coapplicant_itr: Optional[str] = None  # yes, no
    collateral: Optional[str] = None  # yes, no
    visa_timeline: Optional[str] = None
    eligibility_category: Optional[str] = None  # public_secured, private_unsecured, intl_usd, escalate
    sentiment_score: Optional[float] = None
    urgency: Optional[str] = None  # high, medium, low
    status: str = "new"  # new, qualified, handoff, callback, unreachable, converted
    lead_source: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = {}
```

### Call Model

```python
class Call(BaseModel):
    call_id: str = Field(default_factory=lambda: f"call_{uuid.uuid4().hex[:12]}")
    lead_id: str
    call_sid: Optional[str] = None  # Twilio call SID
    direction: str  # inbound, outbound
    status: str  # initiated, connected, in_progress, completed, failed, no_answer
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None  # seconds
    recording_url: Optional[str] = None
    transcript_url: Optional[str] = None
    consent_given: bool = False
    retry_count: int = 0
    error_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### Conversation Model

```python
class Turn(BaseModel):
    turn_id: int
    speaker: str  # agent, user
    text: str
    audio_url: Optional[str] = None
    timestamp: datetime
    intent: Optional[str] = None
    entities: dict = {}
    sentiment_score: Optional[float] = None
    confidence_score: Optional[float] = None

class Conversation(BaseModel):
    conversation_id: str = Field(default_factory=lambda: f"conv_{uuid.uuid4().hex[:12]}")
    call_id: str
    lead_id: str
    language: str
    current_state: str
    turns: list[Turn] = []
    collected_data: dict = {}
    negative_turn_count: int = 0
    clarification_count: int = 0
    escalation_triggered: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Configuration Model

```python
class VoicePrompt(BaseModel):
    prompt_id: str
    state: str  # greeting, degree_question, country_question, etc.
    language: str
    text: str
    audio_url: Optional[str] = None  # Pre-generated TTS audio

class ConversationFlow(BaseModel):
    flow_id: str
    name: str
    states: list[str]
    transitions: dict  # state -> next_state mapping
    prompts: dict  # state -> prompt_id mapping
```

## Error Handling

### Error Categories

1. **Telephony Errors**
   - Call failed to connect
   - Network drop mid-call
   - Busy signal
   - No answer

2. **Speech Processing Errors**
   - ASR confidence too low
   - TTS generation failed
   - Language detection failed
   - Audio quality issues

3. **Business Logic Errors**
   - Invalid data collected
   - Eligibility rules failed
   - CRM integration failed
   - Expert unavailable for handoff

4. **System Errors**
   - Database connection lost
   - External API timeout
   - Service unavailable

### Error Handling Strategy

```python
class ErrorHandler:
    async def handle_telephony_error(call_id: str, error: Exception) -> None:
        """
        - Log error with call context
        - Update call status to failed
        - Schedule retry if applicable (max 3 attempts)
        - Send notification to ops team if critical
        """
    
    async def handle_speech_error(call_id: str, error: Exception) -> None:
        """
        - If ASR failed: Ask user to repeat once
        - If TTS failed: Use fallback pre-recorded audio
        - If language detection failed: Default to English
        - Log error for analysis
        """
    
    async def handle_business_error(call_id: str, error: Exception) -> None:
        """
        - If eligibility failed: Escalate to human
        - If CRM failed: Queue for retry, continue call
        - If expert unavailable: Offer callback scheduling
        - Log error and alert relevant team
        """
    
    async def handle_system_error(call_id: str, error: Exception) -> None:
        """
        - Gracefully end call with apology
        - Schedule immediate callback
        - Alert ops team
        - Log full stack trace
        """
```

### Retry Logic

```python
class RetryPolicy:
    MAX_CALL_RETRIES = 3
    RETRY_INTERVALS = [3600, 21600, 86400]  # 1hr, 6hr, 24hr in seconds
    
    MAX_API_RETRIES = 3
    API_RETRY_BACKOFF = [1, 5, 15]  # seconds
    
    async def should_retry_call(call: Call) -> bool:
        return call.retry_count < MAX_CALL_RETRIES and call.status in ["no_answer", "failed"]
    
    async def schedule_retry(call_id: str, attempt: int) -> None:
        delay = RETRY_INTERVALS[attempt - 1]
        # Schedule background task to retry after delay
```

### Graceful Degradation

- If OpenAI API fails → Fall back to regex-based entity extraction
- If sentiment analysis fails → Use keyword-based detection only
- If TTS fails → Use pre-recorded audio files
- If CRM fails → Store locally and sync later
- If notification fails → Queue for retry

## Testing Strategy

### Unit Tests

**Coverage Target: 80%+**

```python
# Test NLU Engine
def test_intent_detection_hinglish()
def test_intent_detection_english()
def test_entity_extraction_country()
def test_entity_extraction_loan_amount()
def test_confidence_score_calculation()

# Test Eligibility Engine
def test_category_public_secured()
def test_category_private_unsecured()
def test_category_intl_usd()
def test_category_escalate()
def test_urgency_high()
def test_urgency_medium()

# Test Sentiment Analyzer
def test_positive_sentiment()
def test_negative_sentiment()
def test_frustration_keywords()
def test_multilingual_sentiment()

# Test Conversation Manager
def test_state_transitions()
def test_context_management()
def test_language_switching()
def test_escalation_trigger()
```

### Integration Tests

```python
# Test API Endpoints
def test_create_outbound_call()
def test_inbound_webhook_handling()
def test_lead_creation_and_retrieval()
def test_handoff_trigger()

# Test External Integrations
def test_twilio_call_initiation()
def test_google_speech_transcription()
def test_google_tts_synthesis()
def test_whatsapp_notification()
def test_crm_lead_sync()

# Test End-to-End Flows
def test_complete_qualification_flow()
def test_handoff_flow()
def test_retry_flow()
def test_language_switch_flow()
```

### Load Tests

```python
# Simulate concurrent calls
def test_10_concurrent_calls()
def test_50_concurrent_calls()
def test_100_concurrent_calls()

# Measure performance
def test_api_response_time()  # < 200ms
def test_tts_latency()  # < 1.2s
def test_overall_call_latency()  # < 2s
```

### User Acceptance Tests

```python
# Test with real users (beta phase)
- 50 test calls with actual students
- Measure call completion rate (target: 80%)
- Measure qualification time (target: ≤ 3 min)
- Measure handoff rate (target: 55%)
- Collect CSAT scores (target: 4.5/5)
- Verify language accuracy (Hinglish 90%, Telugu 85%)
```

### Test Data

```python
# Sample test leads
TEST_LEADS = [
    {
        "phone": "+919876543210",
        "language": "hinglish",
        "country": "US",
        "degree": "masters",
        "collateral": "yes",
        "expected_category": "public_secured"
    },
    {
        "phone": "+919876543211",
        "language": "english",
        "country": "UK",
        "degree": "bachelors",
        "collateral": "no",
        "coapplicant_itr": "yes",
        "expected_category": "private_unsecured"
    },
    # ... more test cases
]
```

### Monitoring and Observability

```python
# Metrics to track
- Call volume (inbound/outbound)
- Call completion rate
- Average qualification time
- Handoff rate
- Sentiment distribution
- Language detection accuracy
- ASR/TTS latency
- API error rates
- System uptime

# Logging
- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Include call_id, lead_id in all logs for traceability
- Separate logs for: API, telephony, speech, business logic

# Alerts
- Call failure rate > 10%
- API latency > 2s
- System error rate > 5%
- Expert handoff queue > 10
- Database connection issues
```

## Deployment Architecture

### Development Environment

```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb://mongo:27017/voice_agent
      - TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}
      - TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - mongo
  
  mongo:
    image: mongo:6.0
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
```

### Production Environment

- **Container Orchestration**: Kubernetes
- **Load Balancer**: NGINX Ingress
- **Database**: MongoDB Atlas (managed)
- **Secrets Management**: Kubernetes Secrets / AWS Secrets Manager
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **CI/CD**: GitHub Actions → Docker Registry → Kubernetes

### Scalability Considerations

- Horizontal scaling of backend pods based on CPU/memory
- MongoDB sharding for large lead volumes
- Redis cache for frequently accessed data (prompts, configurations)
- CDN for pre-recorded audio files
- Queue system (RabbitMQ/Redis) for async tasks (retries, notifications)

## Security Considerations

1. **Data Encryption**
   - TLS 1.3 for all API communications
   - Encrypt PII fields in MongoDB (field-level encryption)
   - Encrypt call recordings at rest (AES-256)

2. **Authentication & Authorization**
   - JWT tokens for API authentication
   - Role-based access control (RBAC) for frontend users
   - API key authentication for webhooks

3. **PII Protection**
   - Mask phone numbers in logs
   - Anonymize transcripts for training data
   - Implement data retention policies (90 days max)
   - GDPR compliance: Right to deletion, data export

4. **Rate Limiting**
   - API rate limits: 100 req/min per IP
   - Webhook rate limits: 1000 req/min
   - DDoS protection via CloudFlare

5. **Audit Logging**
   - Log all data access and modifications
   - Track user actions in frontend
   - Maintain immutable audit trail
