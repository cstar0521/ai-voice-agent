# Implementation Plan

- [x] 1. Set up project structure and development environment
  - Create monorepo structure with frontend, backend, and shared directories
  - Set up Docker Compose for local development with MongoDB, frontend, and backend services
  - Configure environment variables and secrets management
  - Initialize Git repository with .gitignore for Python and Node.js
  - _Requirements: 8.5_

- [x] 2. Implement core data models and database layer

- [x] 2.1 Create MongoDB connection and configuration
  - Write MongoDB connection utility using Motor (async driver)
  - Implement connection pooling and error handling
  - Create database initialization script

  - _Requirements: 6.2, 6.4_

- [x] 2.2 Implement Pydantic models for Lead, Call, and Conversation
  - Define Lead model with all eligibility fields and validation
  - Define Call model with status tracking and metadata
  - Define Conversation model with turn history and context
  - Define Configuration models for prompts and flows
  - _Requirements: 2.1, 6.1, 6.2_

- [x] 2.3 Create database repository layer
  - Implement LeadRepository with CRUD operations
  - Implement CallRepository with status updates and queries
  - Implement ConversationRepository with turn appending
  - Implement ConfigurationRepository for prompts and flows
  - _Requirements: 6.2_

- [x] 2.4 Write unit tests for data models and repositories
  - Test model validation and serialization
  - Test repository CRUD operations
  - Test database connection error handling
  - _Requirements: 6.2_

- [x] 3. Build FastAPI backend foundation

- [x] 3.1 Create FastAPI application with middleware
  - Initialize FastAPI app with CORS, logging, and error handling middleware
  - Implement request/response logging
  - Set up API versioning (/api/v1)
  - _Requirements: 8.3_

- [x] 3.2 Implement authentication and authorization
  - Create JWT token generation and validation utilities
  - Implement API key authentication for webhooks
  - Add authentication middleware to protect endpoints
  - _Requirements: 11.1_

- [x] 3.3 Create API endpoints for call management
  - POST /api/v1/calls/outbound - Initiate outbound call
  - POST /api/v1/calls/inbound/webhook - Handle Twilio webhook
  - POST /api/v1/calls/{call_id}/hangup - End call
  - GET /api/v1/calls/{call_id} - Get call details
  - GET /api/v1/calls - List calls with pagination and filters
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 3.4 Create API endpoints for lead management
  - GET /api/v1/leads - List leads with filters
  - GET /api/v1/leads/{lead_id} - Get lead details
  - PUT /api/v1/leads/{lead_id} - Update lead
  - POST /api/v1/leads/{lead_id}/handoff - Trigger handoff
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 3.5 Create API endpoints for configuration
  - GET /api/v1/config/prompts - Get voice prompts by language
  - PUT /api/v1/config/prompts - Update prompts
  - GET /api/v1/config/flows - Get conversation flows
  - _Requirements: 1.2, 1.3_

- [x] 3.6 Create API endpoints for analytics
  - GET /api/v1/analytics/metrics - Get KPI metrics
  - GET /api/v1/analytics/calls - Get call analytics with aggregations
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 3.7 Write integration tests for API endpoints
  - Test all endpoints with valid and invalid inputs
  - Test authentication and authorization
  - Test error responses
  - _Requirements: 8.3_

- [x] 4. Implement telephony integration with Twilio

- [x] 4.1 Create Twilio adapter class
  - Implement make_call method for outbound calls
  - Implement answer_call method for inbound calls
  - Implement transfer_call method for expert handoff
  - Implement hangup_call method
  - Implement start_recording and stop_recording methods
  - _Requirements: 5.1, 5.2, 4.3_

- [x] 4.2 Implement webhook handlers for Twilio events
  - Handle call status callbacks (initiated, ringing, answered, completed)
  - Handle recording status callbacks
  - Handle speech recognition results
  - Parse and validate Twilio webhook signatures
  - _Requirements: 5.1, 5.2, 11.2_

- [x] 4.3 Write integration tests for Twilio adapter
  - Mock Twilio API responses
  - Test call initiation and status updates
  - Test webhook signature validation
  - _Requirements: 5.1_

- [x] 5. Implement speech processing integration

- [x] 5.1 Create speech adapter for Google Cloud or AWS
  - Implement transcribe_audio method with streaming support
  - Implement synthesize_speech method with voice selection
  - Implement detect_language method
  - Handle multiple languages (Hinglish, English, Telugu)
  - _Requirements: 1.1, 1.2, 8.1, 8.2_

- [x] 5.1a Integrate Sarvam AI speech adapter for Indian languages
  - Implement SarvamSpeechAdapter class with Sarvam AI API integration
  - Add Sarvam API key configuration to settings
  - Implement transcribe_audio using Sarvam ASR endpoint
  - Implement synthesize_speech using Sarvam TTS endpoint with Indian voice models
  - Add language detection for Hinglish, Hindi, and Telugu
  - Implement fallback to Google Cloud/AWS when Sarvam is unavailable
  - _Requirements: 1.1, 1.2, 8.1, 8.2, 8.6_

- [x] 5.2 Implement audio streaming and buffering
  - Create audio stream handler for real-time ASR
  - Implement audio buffering for TTS responses
  - Handle audio format conversions
  - _Requirements: 8.2, 8.3_

- [x] 5.3 Write integration tests for speech adapter
  - Test transcription with sample audio files
  - Test TTS generation for all languages
  - Test language detection
  - _Requirements: 8.1_

- [x] 6. Build NLU engine for intent and entity extraction

- [x] 6.1 Implement intent detection using OpenAI API
  - Create prompt templates for intent classification
  - Implement Intent enum and detection logic
  - Calculate confidence scores
  - Handle multilingual input (Hinglish, English, Telugu)
  - _Requirements: 2.3, 2.4_

- [x] 6.2 Implement entity extraction
  - Create entity extraction prompts for OpenAI
  - Implement regex-based fallback for simple entities (yes/no, numbers)
  - Extract country, degree, loan_amount, collateral, ITR, visa_timeline
  - Validate extracted entities
  - _Requirements: 2.1, 2.2, 2.5_

- [x] 6.3 Implement confidence scoring and clarification logic
  - Calculate confidence scores for intents and entities
  - Implement clarification trigger when confidence < 0.6
  - Track clarification count per conversation
  - _Requirements: 2.3, 2.4_

- [x] 6.4 Write unit tests for NLU engine
  - Test intent detection with sample utterances
  - Test entity extraction for all entity types
  - Test confidence scoring
  - Test multilingual support
  - _Requirements: 2.3_

- [x] 7. Implement sentiment analysis

- [x] 7.1 Create sentiment analyzer with multiple approaches
  - Implement TextBlob-based sentiment for English
  - Implement OpenAI-based sentiment for Hinglish/Telugu
  - Create keyword-based frustration detection
  - Combine scores: 70% ML + 30% keywords
  - _Requirements: 9.1, 9.2_

- [x] 7.2 Implement sentiment tracking and escalation logic
  - Track sentiment history per conversation
  - Increment negative turn counter when sentiment < -0.3
  - Trigger escalation when negative_turn_count >= 2

  - Detect aggressive/rude tone keywords
  - _Requirements: 9.3, 9.4_

- [x] 7.3 Write unit tests for sentiment analyzer
  - Test positive, neutral, and negative sentiment detection
  - Test frustration keyword detection
  - Test escalation trigger logic
  - _Requirements: 9.1, 9.2_

- [x] 8. Build eligibility engine with business rules

- [x] 8.1 Implement loan category determination
  - Implement determine_category method with all business rules
  - Map collateral + ITR combinations to categories
  - Handle special cases (US/Canada + high merit)
  - Return public_secured, private_unsecured, intl_usd, or escalate
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 8.2 Implement urgency calculation
  - Parse visa_timeline string to extract date
  - Calculate days until visa deadline
  - Return high (<30 days), medium (30-90 days), or low (>90 days)
  - _Requirements: 3.4_

- [x] 8.3 Implement lender recommendations
  - Create lender mapping for each category
  - Return appropriate lenders based on category and urgency
  - Handle fast-track lenders for high urgency
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 8.4 Write unit tests for eligibility engine
  - Test all category determination scenarios
  - Test urgency calculation with various timelines
  - Test lender recommendations
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 9. Implement conversation manager and state machine

- [x] 9.1 Create conversation state machine
  - Define all conversation states (greeting, language_detection, qualification, etc.)
  - Implement state transition logic
  - Create state-to-prompt mapping
  - Handle state persistence in database
  - _Requirements: 1.1, 2.1, 2.2_

- [x] 9.2 Implement conversation context management
  - Create ConversationContext class with all fields
  - Implement context loading and saving
  - Maintain turn history (last 3 minutes)
  - Track collected_data, sentiment_history, negative_turn_count
  - _Requirements: 2.1, 2.5, 9.1_

- [x] 9.3 Implement prompt generation for all states
  - Create prompt templates for each state in all languages
  - Implement dynamic prompt generation based on context
  - Handle language-specific prompts (Hinglish, English, Telugu)
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 9.4 Implement user response processing
  - Process user utterance through NLU engine
  - Extract and validate entities based on current state
  - Update conversation context with collected data
  - Determine next state based on response
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 9.5 Implement language switching logic
  - Detect language switch requests
  - Update conversation language preference
  - Reload prompts in new language
  - Handle mid-call language changes
  - _Requirements: 1.3, 1.4_

- [x] 9.6 Implement escalation detection
  - Check clarification count threshold (>2)
  - Check negative sentiment threshold
  - Check explicit handoff requests
  - Trigger handoff flow when conditions met

  - _Requirements: 2.4, 4.1, 4.2, 9.3_

- [x] 9.7 Write unit tests for conversation manager
  - Test state transitions
  - Test context management
  - Test prompt generation
  - Test language switching
  - Test escalation triggers
  - _Requirements: 2.1, 9.3_

- [x] 10. Build call orchestrator

- [x] 10.1 Implement call lifecycle management
  - Create call state machine (initiated → dialing → connected → completed)
  - Implement state transition handlers
  - Track call metadata (start_time, end_time, duration)
  - Handle call status updates from Twilio
  - _Requirements: 5.1, 5.2, 7.1_

- [x] 10.2 Implement outbound call initiation
  - Create lead record in database
  - Initiate call via Twilio adapter
  - Set up webhook callbacks
  - Start conversation flow on connection
  - _Requirements: 5.1, 7.1_

- [x] 10.3 Implement inbound call handling
  - Answer incoming call via Twilio
  - Create lead record from caller ID
  - Skip greeting, start with intent confirmation
  - Request recording consent
  - _Requirements: 5.1, 5.2, 5.4, 5.5_

- [x] 10.4 Implement call event processing
  - Handle speech detected events
  - Handle silence timeout (>8 seconds)
  - Handle user hangup
  - Handle network errors
  - _Requirements: 9.5, 12.1, 12.2_

- [x] 10.5 Implement retry logic for failed calls
  - Check retry eligibility (max 3 attempts)
  - Schedule retries at 1hr, 6hr, 24hr intervals
  - Update call status and retry_count
  - Mark as unreachable after 3 failed attempts
  - _Requirements: 7.4, 7.5_

- [x] 10.6 Write unit tests for call orchestrator
  - Test call lifecycle state transitions
  - Test outbound and inbound call flows
  - Test retry logic
  - Test error handling
  - _Requirements: 7.1, 7.4_

- [x] 11. Implement human expert handoff

- [x] 11.1 Create handoff trigger logic
  - Detect user request for human expert
  - Detect negative sentiment threshold
  - Detect unclear responses threshold
  - Update lead status to "handoff"
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 11.2 Implement call transfer to expert
  - Check expert availability
  - Transfer call via Twilio adapter
  - Send lead summary to CRM
  - Update call status to "transferred"
  - _Requirements: 4.3, 4.4_

- [x] 11.3 Implement callback scheduling
  - Offer callback when expert unavailable
  - Collect preferred callback time
  - Create callback task in database
  - Send confirmation via WhatsApp/SMS
  - _Requirements: 4.4, 4.5_

- [x] 11.4 Write integration tests for handoff flow
  - Test handoff trigger conditions
  - Test call transfer
  - Test callback scheduling
  - _Requirements: 4.1, 4.3_

- [x] 12. Implement notification system

- [x] 12.1 Create notification adapter for SuprSend/Gupshup
  - Implement send_whatsapp method with template support
  - Implement send_sms method
  - Handle API authentication and error responses
  - _Requirements: 4.5, 7.2, 7.3_

- [x] 12.2 Implement post-call follow-up notifications
  - Send WhatsApp/SMS summary after call completion
  - Include eligibility category and next steps
  - Include callback timing if scheduled
  - _Requirements: 7.2, 7.3_

- [x] 12.3 Implement no-answer follow-up
  - Send text with callback link when call not answered
  - Include retry schedule information
  - _Requirements: 7.3, 7.4_

- [x] 12.4 Write integration tests for notifications
  - Mock notification API responses
  - Test WhatsApp and SMS sending
  - Test error handling
  - _Requirements: 7.2, 7.3_

- [x] 13. Implement CRM integration

- [x] 13.1 Create CRM adapter
  - Implement create_lead method
  - Implement update_lead method
  - Implement get_lead method
  - Implement notify_expert method for handoffs
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 13.2 Implement lead data synchronization
  - Push structured lead summary after qualification
  - Include all collected fields and eligibility data
  - Handle CRM API failures with retry queue
  - _Requirements: 6.1, 6.2_

- [x] 13.3 Implement PII encryption
  - Encrypt sensitive fields before storage
  - Implement field-level encryption for phone, name
  - Mask PII in logs
  - _Requirements: 6.4, 11.3, 11.4_

- [x] 13.4 Write integration tests for CRM adapter
  - Mock CRM API responses
  - Test lead creation and updates
  - Test error handling and retries
  - _Requirements: 6.2_

- [x] 14. Build React frontend dashboard

- [x] 14.1 Set up React project with Material-UI
  - Initialize React app with TypeScript
  - Install Material-UI and other dependencies
  - Set up routing with React Router
  - Configure API client with Axios
  - _Requirements: 10.1_

- [x] 14.2 Create authentication and layout components
  - Implement login page with JWT authentication
  - Create main layout with navigation
  - Implement protected routes
  - Add logout functionality

  - _Requirements: 10.1_

- [x] 14.3 Implement call monitoring dashboard
  - Create real-time call list with status indicators
  - Display active calls with current state

  - Show call duration and language
  - Implement auto-refresh or WebSocket updates
  - _Requirements: 10.1, 10.2_

- [x] 14.4 Implement lead management interface
  - Create lead list with filters (status, date, category)
  - Implement lead detail view with full information
  - Add lead update functionality
  - Show call history per lead
  - _Requirements: 10.1, 10.2_

- [x] 14.5 Create analytics and metrics dashboard
  - Display KPI cards (completion rate, avg time, handoff rate)
  - Create charts for call volume over time

  - Show sentiment distribution
  - Display language usage statistics
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 14.6 Implement configuration management UI
  - Create prompt editor for all languages
  - Implement conversation flow visualizer
  - Add prompt testing interface
  - _Requirements: 10.1_

- [x] 14.7 Write component tests for frontend
  - Test authentication flow
  - Test dashboard components
  - Test lead management
  - _Requirements: 10.1_

- [x] 15. Implement voice prompt management

- [x] 15.1 Create prompt templates for all states
  - Write Hinglish prompts for all conversation states
  - Write English prompts for all conversation states
  - Write Telugu prompts for all conversation states
  - Store prompts in database configuration collection
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 15.2 Implement pre-generated TTS audio caching
  - Generate TTS audio for common prompts
  - Store audio files in cloud storage (S3/GCS)
  - Create audio URL mapping in database

  - Implement fallback to real-time TTS
  - _Requirements: 8.2_

- [x] 15.3 Create prompt versioning system
  - Track prompt versions in database
  - Allow A/B testing of different prompts
  - Implement prompt rollback capability
  - _Requirements: 1.1_

- [x] 16. Implement logging and monitoring

- [x] 16.1 Set up structured logging
  - Configure Python logging with JSON formatter
  - Include call_id and lead_id in all logs
  - Implement log levels (DEBUG, INFO, WARNING, ERROR)
  - Separate logs by component (API, telephony, speech, business)
  - _Requirements: 8.5, 11.4_

- [x] 16.2 Implement metrics collection
  - Track call volume, completion rate, qualification time
  - Track handoff rate, sentiment distribution
  - Track ASR/TTS latency, API error rates
  - Store metrics in database for analytics

  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 16.3 Set up alerting system
  - Create alerts for high error rates (>5%)
  - Alert on high API latency (>2s)
  - Alert on call failure rate (>10%)
  - Send alerts to ops team via email/Slack
  - _Requirements: 8.3, 8.4_

- [x] 17. Implement compliance and security features

- [x] 17.1 Implement consent management
  - Request recording consent at call start
  - Store consent status in call record
  - Disable recording if consent declined
  - _Requirements: 5.4, 5.5, 11.1, 11.2_

- [x] 17.2 Implement data retention policies
  - Create background job to delete old recordings (>90 days)
  - Implement data export for GDPR requests
  - Implement data deletion for GDPR requests
  - _Requirements: 6.4, 11.4_

- [x] 17.3 Implement rate limiting
  - Add rate limiting middleware to API (100 req/min per IP)
  - Implement webhook rate limiting (1000 req/min)
  - Add DDoS protection headers
  - _Requirements: 8.4_

- [x] 17.4 Implement audit logging
  - Log all data access and modifications
  - Track user actions in frontend
  - Create immutable audit trail
  - _Requirements: 11.4_

- [x] 18. Create deployment configuration

- [x] 18.1 Create Docker configurations
  - Write Dockerfile for backend with Python dependencies
  - Write Dockerfile for frontend with Node.js build
  - Create docker-compose.yml for local development
  - Configure environment variables and secrets
  - _Requirements: 8.4_

- [x] 18.2 Create Kubernetes manifests
  - Write deployment manifests for backend and frontend
  - Create service and ingress configurations
  - Configure ConfigMaps and Secrets
  - Set up horizontal pod autoscaling
  - _Requirements: 8.4_

- [x] 18.3 Set up CI/CD pipeline
  - Create GitHub Actions workflow for testing
  - Add Docker image building and pushing
  - Implement automated deployment to staging
  - Add manual approval for production deployment
  - _Requirements: 8.4_

- [x] 19. Perform integration and end-to-end testing

- [x] 19.1 Create end-to-end test scenarios
  - Test complete outbound call flow (greeting to handoff)
  - Test complete inbound call flow
  - Test language switching mid-call
  - Test retry flow for failed calls
  - Test handoff flow with expert transfer
  - _Requirements: 1.1, 2.1, 4.1, 7.4_

- [x] 19.2 Conduct load testing
  - Test 10 concurrent calls
  - Test 50 concurrent calls
  - Measure API response times
  - Measure TTS latency and overall call latency
  - _Requirements: 8.2, 8.3_

- [x] 19.3 Perform user acceptance testing
  - Conduct 50 beta calls with real students
  - Measure call completion rate (target: 80%)
  - Measure qualification time (target: ≤3 min)
  - Measure handoff rate (target: 55%)
  - Collect CSAT scores (target: 4.5/5)
  - Verify language accuracy (Hinglish 90%, English 90%, Telugu 85%)
  - _Requirements: 8.1, 10.1, 10.2, 10.3, 10.4_

- [x] 20. Create documentation and deployment guide

- [x] 20.1 Write API documentation
  - Document all REST endpoints with request/response examples
  - Create OpenAPI/Swagger specification
  - Document webhook payloads
  - _Requirements: 10.1_

- [x] 20.2 Write deployment guide
  - Document local development setup
  - Document production deployment steps
  - Create troubleshooting guide
  - Document monitoring and alerting setup
  - _Requirements: 8.4_

- [x] 20.3 Create operator runbook
  - Document common issues and resolutions
  - Create escalation procedures
  - Document backup and recovery procedures
  - _Requirements: 8.4_
