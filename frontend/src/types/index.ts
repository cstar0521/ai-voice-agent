export interface Lead {
  lead_id: string;
  name?: string;
  phone: string;
  language: string;
  country?: string;
  degree?: string;
  loan_amount?: number;
  offer_letter?: string;
  coapplicant_itr?: string;
  collateral?: string;
  visa_timeline?: string;
  eligibility_category?: string;
  sentiment_score?: number;
  urgency?: string;
  status: string;
  lead_source?: string;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

export interface Call {
  call_id: string;
  lead_id: string;
  call_sid?: string;
  direction: 'inbound' | 'outbound';
  status: string;
  start_time?: string;
  end_time?: string;
  duration?: number;
  recording_url?: string;
  transcript_url?: string;
  consent_given: boolean;
  retry_count: number;
  error_reason?: string;
  created_at: string;
}

export interface Turn {
  turn_id: number;
  speaker: 'agent' | 'user';
  text: string;
  audio_url?: string;
  timestamp: string;
  intent?: string;
  entities?: Record<string, any>;
  sentiment_score?: number;
  confidence_score?: number;
}

export interface Conversation {
  conversation_id: string;
  call_id: string;
  lead_id: string;
  language: string;
  current_state: string;
  turns: Turn[];
  collected_data: Record<string, any>;
  negative_turn_count: number;
  clarification_count: number;
  escalation_triggered: boolean;
  created_at: string;
  updated_at: string;
}

export interface VoicePrompt {
  prompt_id: string;
  state: string;
  language: string;
  text: string;
  audio_url?: string;
}

export interface Metrics {
  call_completion_rate: number;
  avg_qualification_time: number;
  handoff_rate: number;
  total_calls: number;
  active_calls: number;
  sentiment_distribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
  language_usage: Record<string, number>;
}

export interface User {
  username: string;
  role: string;
  token?: string;
}
