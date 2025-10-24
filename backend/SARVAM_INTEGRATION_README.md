# Sarvam AI Integration Guide

## Overview

The AI Voice Loan Agent now supports Sarvam AI as a speech provider for Indian languages (Hinglish, Hindi, Telugu, and more). Sarvam AI provides optimized ASR (Automatic Speech Recognition) and TTS (Text-to-Speech) services for Indian languages.

## Configuration

### 1. Environment Variables

Add the following to your `backend/.env` file:

```env
# Speech Provider (sarvam_ai, google_cloud, or aws)
SPEECH_PROVIDER=sarvam_ai

# Sarvam AI Configuration
SARVAM_API_KEY=your_sarvam_api_key_here
SARVAM_API_URL=https://api.sarvam.ai/v1
```

### 2. API Key

Your Sarvam API key has been configured:
- Format: `sk_***********************`
- Location: `backend/.env`

## Implementation

### Speech Adapter

The `SarvamAISpeechAdapter` class has been implemented in `backend/app/integrations/speech_adapter.py` with the following features:

#### Supported Operations

1. **Text-to-Speech (TTS)**
   - Converts text to speech audio
   - Supports multiple Indian languages
   - Female and male voice options (Meera, Arvind)
   - Adjustable speaking rate

2. **Speech-to-Text (ASR)**
   - Transcribes audio to text
   - Real-time streaming support
   - Multi-language support

3. **Language Detection**
   - Automatically detects spoken language
   - Supports 10+ Indian languages

4. **Translation**
   - Translates text between Indian languages
   - Useful for multilingual conversations

### Usage Example

```python
from app.integrations.speech_adapter import create_speech_adapter

# Create Sarvam AI adapter
adapter = create_speech_adapter("sarvam_ai")

# Text-to-Speech
audio_bytes = await adapter.synthesize_speech(
    text="नमस्ते, मैं आपकी मदद के लिए यहाँ हूँ",
    language="hi-IN",
    voice_gender=VoiceGender.FEMALE
)

# Speech-to-Text
result = await adapter.transcribe_audio(
    audio_data=audio_bytes,
    language="hi-IN"
)
print(result["transcript"])

# Language Detection
detected_lang = await adapter.detect_language(audio_bytes)
print(f"Detected: {detected_lang}")

# Translation
translated = await adapter.translate_text(
    text="Hello, how are you?",
    source_lang="en-IN",
    target_lang="hi-IN"
)
```

## Supported Languages

The adapter supports the following Indian languages:

- Hindi (hi-IN) / Hinglish
- English (en-IN) - Indian English
- Telugu (te-IN)
- Tamil (ta-IN)
- Kannada (kn-IN)
- Malayalam (ml-IN)
- Marathi (mr-IN)
- Gujarati (gu-IN)
- Bengali (bn-IN)
- Punjabi (pa-IN)

## API Endpoints

The implementation uses the following Sarvam AI API endpoints:

- `/text-to-speech` - TTS generation
- `/speech-to-text` - ASR transcription
- `/speech-to-text-stream` - Streaming ASR
- `/language-detection` - Language identification
- `/translate` - Text translation

## Troubleshooting

### 404 Not Found Errors

If you encounter 404 errors when testing the API:

1. **Verify API Key**: Ensure your Sarvam API key is valid and active
2. **Check API Documentation**: Sarvam AI may have updated their API endpoints
3. **Contact Sarvam Support**: Reach out to Sarvam AI support for the latest API documentation
4. **API Access**: Confirm your API key has access to the required endpoints

### Testing the Integration

Run the test script to verify the integration:

```bash
cd backend
python test_sarvam_integration.py
```

### Fallback to Google Cloud

If Sarvam AI is unavailable, the system can fall back to Google Cloud:

```env
SPEECH_PROVIDER=google_cloud
```

## Next Steps

1. **Verify API Key**: Contact Sarvam AI to confirm your API key is active
2. **Get API Documentation**: Request the latest API documentation from Sarvam
3. **Update Endpoints**: Modify the adapter if endpoints have changed
4. **Test with Real Audio**: Test with actual audio files once the API is accessible

## Implementation Status

✅ Configuration added to settings
✅ SarvamAISpeechAdapter class implemented
✅ Factory function updated to support Sarvam AI
✅ Language mapping for Indian languages
✅ Error handling and logging
✅ Fallback to Google Cloud/AWS

⏳ Pending: Valid API key and endpoint verification with Sarvam AI

## Support

For issues with the Sarvam AI integration:
- Check the logs in `backend/logs/`
- Review error messages in the console
- Contact Sarvam AI support: https://www.sarvam.ai/contact

For code-related issues:
- Review `backend/app/integrations/speech_adapter.py`
- Check configuration in `backend/config.py`
- Verify environment variables in `backend/.env`
