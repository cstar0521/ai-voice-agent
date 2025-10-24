# AI Voice Loan Agent - API Documentation

## Overview

The AI Voice Loan Agent API provides RESTful endpoints for managing voice calls, leads, configuration, and analytics. All endpoints use JSON for request/response payloads and require authentication via JWT tokens or API keys for webhooks.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.voiceloanagent.com`

## Authentication

### JWT Authentication (Frontend)

Include the JWT token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

### API Key Authentication (Webhooks)

Include the API key in the X-API-Key header:

```
X-API-Key: <api_key>
```

## API Endpoints

### Call Management

#### Initiate Outbound Call

**POST** `/api/v1/calls/outbound`

Initiates an outbound call to a lead's phone number.

**Request Body:**

```json
{
  "phone_number": "+919876543210",
  "lead_source": "facebook_ad",
  "preferred_language": "hinglish",
  "metadata": {
    "campaign_id": "summer_2025",
    "utm_source": "facebook"
  }
}
```

**Response:**

```json
{
  "call_id": "call_abc123def456",
  "lead_id": "lead_xyz789abc123",
  "status": "initiated",
  "created_at": "2025-10-24T10:30:00Z",
  "estimated_callback_time": "2025-10-24T10:31:00Z"
}
```

**Status Codes:**

- `201`: Call initiated successfully
- `400`: Invalid phone number or request data
- `429`: Rate limit exceeded
- `500`: Internal server error

#### Handle Inbound Call Webhook

**POST** `/api/v1/calls/inbound/webhook`

Webhook endpoint for Twilio to handle inbound calls.

**Request Body (Twilio Webhook):**

```json
{
  "CallSid": "CA1234567890abcdef1234567890abcdef",
  "From": "+919876543210",
  "To": "+911234567890",
  "CallStatus": "ringing",
  "Direction": "inbound"
}
```

**Response:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-IN">
        Hello! I'm your AI loan advisor. Are you interested in education loans for studying abroad?
    </Say>
    <Gather input="speech" timeout="10" speechTimeout="auto">
        <Say>Please say yes or no.</Say>
    </Gather>
</Response>
```

#### End Call

**POST** `/api/v1/calls/{call_id}/hangup`

Terminates an active call.

**Path Parameters:**

- `call_id`: Unique identifier for the call

**Response:**

```json
{
  "call_id": "call_abc123def456",
  "status": "completed",
  "end_time": "2025-10-24T10:35:00Z",
  "duration": 300
}
```

#### Get Call Details

**GET** `/api/v1/calls/{call_id}`

Retrieves detailed information about a specific call.

**Path Parameters:**

- `call_id`: Unique identifier for the call

**Response:**

```json
{
  "call_id": "call_abc123def456",
  "lead_id": "lead_xyz789abc123",
  "call_sid": "CA1234567890abcdef1234567890abcdef",
  "direction": "outbound",
  "status": "completed",
  "start_time": "2025-10-24T10:30:00Z",
  "end_time": "2025-10-24T10:35:00Z",
  "duration": 300,
  "recording_url": "https://api.twilio.com/recordings/RE123.mp3",
  "transcript_url": "https://storage.googleapis.com/transcripts/call_abc123.txt",
  "consent_given": true,
  "retry_count": 0,
  "language": "hinglish",
  "sentiment_score": 0.7,
  "qualification_completed": true
}
```

#### List Calls

**GET** `/api/v1/calls`

Retrieves a paginated list of calls with optional filters.

**Query Parameters:**

- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)
- `status`: Filter by call status (initiated, connected, completed, failed)
- `direction`: Filter by direction (inbound, outbound)
- `date_from`: Filter calls from date (ISO 8601)
- `date_to`: Filter calls to date (ISO 8601)
- `language`: Filter by language (hinglish, english, telugu)

**Example Request:**

```
GET /api/v1/calls?page=1&limit=10&status=completed&date_from=2025-10-24T00:00:00Z
```

**Response:**

```json
{
  "calls": [
    {
      "call_id": "call_abc123def456",
      "lead_id": "lead_xyz789abc123",
      "direction": "outbound",
      "status": "completed",
      "start_time": "2025-10-24T10:30:00Z",
      "duration": 300,
      "language": "hinglish",
      "qualification_completed": true
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 150,
    "pages": 15
  }
}
```

### Lead Management

#### List Leads

**GET** `/api/v1/leads`

Retrieves a paginated list of leads with optional filters.

**Query Parameters:**

- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)
- `status`: Filter by lead status (new, qualified, handoff, callback, unreachable, converted)
- `category`: Filter by eligibility category (public_secured, private_unsecured, intl_usd, escalate)
- `country`: Filter by destination country
- `urgency`: Filter by urgency level (high, medium, low)
- `date_from`: Filter leads from date (ISO 8601)
- `date_to`: Filter leads to date (ISO 8601)

**Response:**

```json
{
  "leads": [
    {
      "lead_id": "lead_xyz789abc123",
      "name": "Rahul Sharma",
      "phone": "+919876543210",
      "language": "hinglish",
      "country": "US",
      "degree": "masters",
      "loan_amount": 5000000,
      "eligibility_category": "public_secured",
      "urgency": "high",
      "status": "qualified",
      "sentiment_score": 0.8,
      "created_at": "2025-10-24T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 500,
    "pages": 25
  }
}
```

#### Get Lead Details

**GET** `/api/v1/leads/{lead_id}`

Retrieves detailed information about a specific lead.

**Response:**

```json
{
  "lead_id": "lead_xyz789abc123",
  "name": "Rahul Sharma",
  "phone": "+919876543210",
  "language": "hinglish",
  "country": "US",
  "degree": "masters",
  "loan_amount": 5000000,
  "offer_letter": "yes",
  "coapplicant_itr": "yes",
  "collateral": "yes",
  "visa_timeline": "2025-12-15",
  "eligibility_category": "public_secured",
  "sentiment_score": 0.8,
  "urgency": "high",
  "status": "qualified",
  "lead_source": "facebook_ad",
  "created_at": "2025-10-24T10:30:00Z",
  "updated_at": "2025-10-24T10:35:00Z",
  "calls": [
    {
      "call_id": "call_abc123def456",
      "status": "completed",
      "duration": 300,
      "start_time": "2025-10-24T10:30:00Z"
    }
  ],
  "metadata": {
    "campaign_id": "summer_2025",
    "utm_source": "facebook"
  }
}
```

#### Update Lead

**PUT** `/api/v1/leads/{lead_id}`

Updates lead information.

**Request Body:**

```json
{
  "name": "Rahul Kumar Sharma",
  "status": "handoff",
  "notes": "Customer requested callback at 2 PM"
}
```

**Response:**

```json
{
  "lead_id": "lead_xyz789abc123",
  "updated_fields": ["name", "status", "notes"],
  "updated_at": "2025-10-24T11:00:00Z"
}
```

#### Trigger Handoff

**POST** `/api/v1/leads/{lead_id}/handoff`

Initiates handoff process to human expert.

**Request Body:**

```json
{
  "reason": "customer_request",
  "expert_id": "expert_123",
  "priority": "high",
  "notes": "Customer has complex visa timeline requirements"
}
```

**Response:**

```json
{
  "handoff_id": "handoff_def456ghi789",
  "lead_id": "lead_xyz789abc123",
  "expert_id": "expert_123",
  "status": "queued",
  "estimated_callback_time": "2025-10-24T12:00:00Z",
  "created_at": "2025-10-24T11:00:00Z"
}
```

### Configuration Management

#### Get Voice Prompts

**GET** `/api/v1/config/prompts`

Retrieves voice prompts by language and state.

**Query Parameters:**

- `language`: Filter by language (hinglish, english, telugu)
- `state`: Filter by conversation state (greeting, degree_question, etc.)

**Response:**

```json
{
  "prompts": [
    {
      "prompt_id": "greeting_hinglish_001",
      "state": "greeting",
      "language": "hinglish",
      "text": "Namaste! Main aapka AI loan advisor hun. Kya aap study abroad ke liye education loan ke baare mein jaanna chahte hain?",
      "audio_url": "https://storage.googleapis.com/audio/greeting_hinglish_001.mp3",
      "version": "1.2",
      "created_at": "2025-10-24T10:00:00Z"
    }
  ]
}
```

#### Update Prompts

**PUT** `/api/v1/config/prompts`

Updates voice prompts for specific states and languages.

**Request Body:**

```json
{
  "prompts": [
    {
      "prompt_id": "greeting_hinglish_001",
      "text": "Namaste! Main aapka AI loan advisor hun. Study abroad ke liye loan chahiye?",
      "regenerate_audio": true
    }
  ]
}
```

**Response:**

```json
{
  "updated_prompts": [
    {
      "prompt_id": "greeting_hinglish_001",
      "status": "updated",
      "audio_generation_status": "queued"
    }
  ]
}
```

#### Get Conversation Flows

**GET** `/api/v1/config/flows`

Retrieves conversation flow configurations.

**Response:**

```json
{
  "flows": [
    {
      "flow_id": "outbound_qualification_v2",
      "name": "Outbound Qualification Flow",
      "states": [
        "greeting",
        "language_detection",
        "degree_question",
        "country_question",
        "loan_amount_question",
        "offer_letter_question",
        "coapplicant_question",
        "collateral_question",
        "visa_timeline_question",
        "eligibility_summary",
        "handoff_offer"
      ],
      "transitions": {
        "greeting": "language_detection",
        "language_detection": "degree_question",
        "degree_question": "country_question"
      },
      "version": "2.1",
      "active": true
    }
  ]
}
```

### Analytics

#### Get KPI Metrics

**GET** `/api/v1/analytics/metrics`

Retrieves key performance indicator metrics.

**Query Parameters:**

- `date_from`: Start date for metrics (ISO 8601)
- `date_to`: End date for metrics (ISO 8601)
- `granularity`: Time granularity (hour, day, week, month)

**Response:**

```json
{
  "metrics": {
    "call_volume": {
      "total": 1250,
      "inbound": 450,
      "outbound": 800
    },
    "completion_rate": 0.82,
    "qualification_time_avg": 165,
    "handoff_rate": 0.55,
    "sentiment_distribution": {
      "positive": 0.65,
      "neutral": 0.25,
      "negative": 0.1
    },
    "language_usage": {
      "hinglish": 0.7,
      "english": 0.25,
      "telugu": 0.05
    },
    "eligibility_categories": {
      "public_secured": 0.4,
      "private_unsecured": 0.35,
      "intl_usd": 0.15,
      "escalate": 0.1
    }
  },
  "period": {
    "from": "2025-10-24T00:00:00Z",
    "to": "2025-10-24T23:59:59Z"
  }
}
```

#### Get Call Analytics

**GET** `/api/v1/analytics/calls`

Retrieves detailed call analytics with aggregations.

**Query Parameters:**

- `date_from`: Start date (ISO 8601)
- `date_to`: End date (ISO 8601)
- `group_by`: Grouping dimension (hour, day, language, country, status)
- `metrics`: Comma-separated metrics (volume, duration, completion_rate)

**Response:**

```json
{
  "analytics": [
    {
      "dimension": "2025-10-24T10:00:00Z",
      "call_volume": 45,
      "avg_duration": 280,
      "completion_rate": 0.84,
      "handoff_rate": 0.52
    },
    {
      "dimension": "2025-10-24T11:00:00Z",
      "call_volume": 52,
      "avg_duration": 295,
      "completion_rate": 0.88,
      "handoff_rate": 0.58
    }
  ],
  "summary": {
    "total_calls": 1250,
    "avg_completion_rate": 0.82,
    "avg_duration": 287
  }
}
```

## Webhook Payloads

### Twilio Call Status Webhook

**Endpoint:** `POST /api/v1/calls/inbound/webhook`

**Payload:**

```json
{
  "CallSid": "CA1234567890abcdef1234567890abcdef",
  "AccountSid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "From": "+919876543210",
  "To": "+911234567890",
  "CallStatus": "completed",
  "Direction": "inbound",
  "Duration": "300",
  "RecordingUrl": "https://api.twilio.com/recordings/RE123.mp3",
  "Timestamp": "2025-10-24T10:35:00Z"
}
```

### Speech Recognition Webhook

**Endpoint:** `POST /api/v1/speech/transcription`

**Payload:**

```json
{
  "call_id": "call_abc123def456",
  "transcript": "Haan, mujhe US mein masters ke liye loan chahiye",
  "confidence": 0.92,
  "language": "hinglish",
  "duration": 3.5,
  "timestamp": "2025-10-24T10:32:15Z"
}
```

## Error Responses

All API endpoints return consistent error responses:

```json
{
  "error": {
    "code": "INVALID_PHONE_NUMBER",
    "message": "The provided phone number is not valid",
    "details": {
      "field": "phone_number",
      "value": "+91invalid"
    }
  },
  "request_id": "req_abc123def456",
  "timestamp": "2025-10-24T10:30:00Z"
}
```

### Common Error Codes

- `INVALID_REQUEST`: Malformed request body or parameters
- `UNAUTHORIZED`: Missing or invalid authentication
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `RATE_LIMITED`: Too many requests
- `INVALID_PHONE_NUMBER`: Phone number format invalid
- `CALL_IN_PROGRESS`: Cannot modify active call
- `EXPERT_UNAVAILABLE`: No experts available for handoff
- `EXTERNAL_SERVICE_ERROR`: Third-party service failure

## Rate Limits

- **API Endpoints**: 100 requests per minute per IP
- **Webhook Endpoints**: 1000 requests per minute
- **Call Initiation**: 10 calls per minute per account

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1635123600
```

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:

- **Development**: `http://localhost:8000/docs`
- **Production**: `https://api.voiceloanagent.com/docs`

Interactive API documentation (Swagger UI) is available at:

- **Development**: `http://localhost:8000/redoc`
- **Production**: `https://api.voiceloanagent.com/redoc`
