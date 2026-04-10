from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    mongodb_uri: str = "mongodb://localhost:27017/voice_agent"
    
    # Twilio
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # OpenAI
    openai_api_key: Optional[str] = None
    
    # Groq (Primary LLM - cheaper alternative)
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.1-8b-instant"  # Fast and cheap model
    use_groq_primary: bool = True  # Use Groq first, fallback to OpenAI
    
    # Speech Provider
    speech_provider: str = "sarvam_ai"  # sarvam_ai, google_cloud, or aws
    
    # Sarvam AI
    sarvam_api_key: Optional[str] = None
    sarvam_api_url: str = "https://api.sarvam.ai"
    
    # Sarvam AI Model Configuration
    sarvam_tts_model: str = "bulbul:v1"
    sarvam_asr_model: str = "saaras:v1"
    sarvam_voice_speaker: str = "meera"
    
    # Google Cloud
    google_cloud_project: Optional[str] = None
    google_application_credentials: Optional[str] = None
    
    # AWS
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    
    # Notifications
    suprsend_api_key: Optional[str] = None
    gupshup_api_key: Optional[str] = None
    
    # Security
    jwt_secret_key: str = "change-this-to-a-secure-secret-key"
    api_key: Optional[str] = None
    
    # Alerting
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    alert_email_from: str = "alerts@voiceagent.com"
    alert_email_to: str = ""  # Comma-separated list
    slack_webhook_url: Optional[str] = None
    
    # Audio Caching
    audio_cache_enabled: bool = True
    audio_cache_base_url: Optional[str] = None
    cloud_provider: str = "local"  # local, gcp, aws
    gcs_bucket_name: Optional[str] = None
    s3_bucket_name: Optional[str] = None
    base_url: str = "http://localhost:8000"
    
    # Environment
    environment: str = "development"
    
    # Logging
    log_level: str = "INFO"
    
    # Webhook URLs (for ngrok in development)
    webhook_base_url: Optional[str] = None  # Set this to your ngrok URL
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
