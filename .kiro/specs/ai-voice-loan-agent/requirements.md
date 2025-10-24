# Requirements Document

## Introduction

The AI Voice Loan Agent is a multilingual voice-based system that qualifies students and working professionals exploring study-abroad education loans. The system handles both inbound and outbound calls, collects eligibility data, answers FAQs, and transfers qualified leads to human loan experts. The agent supports Hinglish, English, and Telugu languages with a warm, professional female voice persona.

## Glossary

- **Voice Agent**: The AI-powered conversational system that conducts phone calls with students
- **ASR (Automatic Speech Recognition)**: Technology that converts spoken language into text
- **TTS (Text-to-Speech)**: Technology that converts text into spoken language
- **NLU (Natural Language Understanding)**: Component that interprets user intent from text
- **Sarvam AI**: Indian language AI platform providing ASR and TTS services optimized for Hinglish, Hindi, and other Indian languages
- **Lead**: A potential customer (student or professional) seeking education loan information
- **Qualification**: The process of collecting eligibility data to determine loan category
- **Handoff**: The process of transferring a call from the AI agent to a human expert
- **CRM (Customer Relationship Management)**: System that stores and manages lead data
- **Hinglish**: A hybrid language mixing Hindi and English
- **Co-applicant**: A person (typically parent) who co-signs the loan application
- **ITR (Income Tax Return)**: Annual tax filing document used to verify income
- **Collateral**: Property or assets pledged as security for a loan
- **Sentiment Score**: A numerical measure of the user's emotional state during the call
- **Eligibility Category**: Classification of loan type (public secured, private unsecured, international USD, or escalate)

## Requirements

### Requirement 1

**User Story:** As a student exploring study-abroad loans, I want to receive a call from an AI agent in my preferred language, so that I can understand loan options without language barriers

#### Acceptance Criteria

1. WHEN the Voice Agent initiates an outbound call, THE Voice Agent SHALL greet the user and state its purpose within 5 seconds of call connection
2. WHEN the Voice Agent detects the user's language preference through speech patterns, THE Voice Agent SHALL switch to the detected language within 2 seconds
3. WHERE the user explicitly requests a language change, THE Voice Agent SHALL transition to the requested language (Hinglish, English, or Telugu) within 2 seconds
4. WHEN the ASR confidence score falls below 0.6 for the current language, THE Voice Agent SHALL automatically switch to English as the fallback language
5. THE Voice Agent SHALL maintain consistent language throughout the call unless the user requests a change

### Requirement 2

**User Story:** As a student, I want the AI agent to collect my eligibility information efficiently, so that I can quickly understand which loan options are available to me

#### Acceptance Criteria

1. THE Voice Agent SHALL collect the following data points in sequence: degree level, country of study, offer letter status, loan amount, co-applicant ITR status, collateral availability, and visa timeline
2. WHEN the Voice Agent completes data collection, THE Voice Agent SHALL finish the qualification process within 3 minutes from call start
3. WHEN the user provides an unclear or ambiguous response, THE Voice Agent SHALL request clarification once before proceeding
4. IF the user provides unclear responses more than 2 times, THEN THE Voice Agent SHALL offer to transfer the call to a human expert
5. THE Voice Agent SHALL store all collected data in structured format with field validation before CRM submission

### Requirement 3

**User Story:** As a student, I want the AI agent to map my eligibility to the right loan category, so that I receive relevant lender recommendations

#### Acceptance Criteria

1. WHEN the user confirms collateral availability, THE Voice Agent SHALL categorize the lead as "public_secured" for public bank secured loans
2. WHEN the user has no collateral AND confirms co-applicant ITR availability, THE Voice Agent SHALL categorize the lead as "private_unsecured" for NBFC loans
3. WHEN the user's country is US or Canada AND the user has high merit, THE Voice Agent SHALL categorize the lead as "intl_usd" for international lenders
4. WHEN the user has visa timeline less than 30 days, THE Voice Agent SHALL flag the lead as "high" urgency for fast-track lenders
5. IF the user has no ITR AND no collateral, THEN THE Voice Agent SHALL categorize the lead as "escalate" and transfer to human expert

### Requirement 4

**User Story:** As a student, I want to speak with a human expert when I need detailed guidance, so that I can get personalized advice for my situation

#### Acceptance Criteria

1. WHEN the user explicitly requests to speak with a person, THE Voice Agent SHALL initiate the handoff process within 5 seconds
2. WHEN the sentiment score indicates negative sentiment for more than 2 consecutive turns, THE Voice Agent SHALL automatically offer human expert transfer
3. WHEN initiating handoff, THE Voice Agent SHALL send the lead summary to the CRM system before transferring the call
4. IF no human expert is available, THEN THE Voice Agent SHALL offer to schedule a callback within 1 hour
5. WHEN handoff is completed, THE Voice Agent SHALL send a confirmation message via WhatsApp or SMS within 5 minutes

### Requirement 5

**User Story:** As a student receiving an inbound call, I want to quickly connect with the AI agent when I click "Call Now", so that I can get immediate assistance

#### Acceptance Criteria

1. WHEN a user initiates an inbound call, THE Voice Agent SHALL answer within 3 rings
2. THE Voice Agent SHALL skip the outbound greeting and directly ask for the user's study-abroad intent
3. WHEN the inbound call is connected, THE Voice Agent SHALL follow the same qualification flow as outbound calls
4. THE Voice Agent SHALL request call recording consent within the first 15 seconds of the call
5. IF the user declines consent, THEN THE Voice Agent SHALL continue the call without recording but log the interaction metadata

### Requirement 6

**User Story:** As a loan counselor, I want to receive structured lead data from the AI agent, so that I can provide informed guidance without repeating questions

#### Acceptance Criteria

1. WHEN the Voice Agent completes qualification, THE Voice Agent SHALL push a structured lead summary to the CRM system within 10 seconds
2. THE Voice Agent SHALL include all collected fields: name, phone, language, country, degree, loan amount, offer letter status, co-applicant ITR, collateral, visa timeline, eligibility category, urgency, and sentiment score
3. WHEN a handoff occurs, THE Voice Agent SHALL transmit the lead summary to the human expert's interface before call transfer
4. THE Voice Agent SHALL encrypt all PII (Personally Identifiable Information) data before storage
5. THE Voice Agent SHALL retain call recordings and transcripts for a maximum of 90 days for training purposes only with user consent

### Requirement 7

**User Story:** As a student, I want to receive follow-up information after the call, so that I have a record of the conversation and next steps

#### Acceptance Criteria

1. WHEN the call ends with a scheduled callback, THE Voice Agent SHALL send a WhatsApp or SMS summary within 5 minutes
2. THE Voice Agent SHALL include the following in the follow-up message: eligibility category, next steps, and callback timing
3. WHEN the user does not answer the call, THE Voice Agent SHALL send a follow-up text with a callback link within 10 minutes
4. THE Voice Agent SHALL retry unanswered calls a maximum of 3 times at intervals of 1 hour, 6 hours, and 24 hours
5. WHEN 3 retry attempts fail, THE Voice Agent SHALL mark the lead as "unreachable" in the CRM system

### Requirement 8

**User Story:** As a system administrator, I want the voice agent to maintain high accuracy and low latency, so that users have a smooth conversational experience

#### Acceptance Criteria

1. THE Voice Agent SHALL achieve ASR accuracy of at least 90 percent for Hinglish and English, and 85 percent for Telugu
2. THE Voice Agent SHALL generate TTS responses with latency less than 1.2 seconds per turn
3. THE Voice Agent SHALL maintain overall call latency less than 2 seconds between user utterance and agent response
4. THE Voice Agent SHALL maintain system availability of 99.5 percent
5. WHEN background noise is detected, THE Voice Agent SHALL request the user to repeat once, and if still unclear, offer to reschedule the call
6. WHERE Sarvam AI is configured as the speech provider, THE Voice Agent SHALL use Sarvam AI for ASR and TTS operations for Indian languages

### Requirement 9

**User Story:** As a student, I want the AI agent to detect when I'm frustrated or confused, so that I can quickly get human assistance

#### Acceptance Criteria

1. THE Voice Agent SHALL calculate a real-time sentiment score for each user turn
2. WHEN the sentiment score indicates negative sentiment, THE Voice Agent SHALL increment a negative turn counter
3. WHEN the negative turn counter reaches 2, THE Voice Agent SHALL offer immediate transfer to a human expert
4. WHEN the user exhibits aggressive or rude tone, THE Voice Agent SHALL respond with a calming statement and offer human transfer
5. WHEN silence exceeds 8 seconds, THE Voice Agent SHALL ask if the user wants to continue or reschedule

### Requirement 10

**User Story:** As a product manager, I want to track key performance metrics, so that I can measure the agent's effectiveness and identify improvement areas

#### Acceptance Criteria

1. THE Voice Agent SHALL log the call completion rate for each call session
2. THE Voice Agent SHALL record the qualification time from call start to data collection completion
3. THE Voice Agent SHALL track the handoff rate (percentage of calls transferred to human experts)
4. THE Voice Agent SHALL capture user satisfaction scores when available post-handoff
5. THE Voice Agent SHALL measure language detection accuracy for each supported language

### Requirement 11

**User Story:** As a compliance officer, I want the system to handle user data securely and obtain proper consent, so that we meet regulatory requirements

#### Acceptance Criteria

1. THE Voice Agent SHALL request explicit consent for call recording within the first 15 seconds of the call
2. WHEN the user declines recording consent, THE Voice Agent SHALL disable recording but continue the call
3. THE Voice Agent SHALL encrypt all call recordings and transcripts using industry-standard encryption
4. THE Voice Agent SHALL mask PII data in transcripts used for training purposes
5. THE Voice Agent SHALL comply with GDPR and RBI data localization guidelines for data storage and retention

### Requirement 12

**User Story:** As a student, I want the AI agent to handle call failures gracefully, so that I don't lose my progress or have a frustrating experience

#### Acceptance Criteria

1. WHEN a network drop occurs mid-call, THE Voice Agent SHALL attempt to re-dial the user after a 10-minute interval
2. WHEN the user's response is unclear due to background noise, THE Voice Agent SHALL repeat the question once before offering to reschedule
3. IF the ASR confidence score is below 0.6 for 2 consecutive turns, THEN THE Voice Agent SHALL offer to switch languages or transfer to human expert
4. WHEN a system error occurs, THE Voice Agent SHALL log the error details and send an alert to the technical team
5. THE Voice Agent SHALL preserve conversation context for 3 minutes to handle brief interruptions
