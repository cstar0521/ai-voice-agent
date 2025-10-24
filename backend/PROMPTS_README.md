# Voice Prompt Management System

This document describes the voice prompt management system for the AI Voice Loan Agent.

## Overview

The system provides comprehensive prompt management with:
- Multi-language support (Hinglish, English, Telugu)
- 18 conversation states with tailored prompts
- TTS audio caching for improved performance
- Version control for A/B testing
- Rollback capabilities

## Conversation States

The system supports the following conversation states:

1. **greeting** - Initial greeting when call connects
2. **intent_confirmation** - Confirm user's interest in education loans
3. **degree_question** - Ask about degree type (Bachelors/Masters/MBA)
4. **country_question** - Ask about destination country
5. **loan_amount_question** - Ask about required loan amount
6. **offer_letter_question** - Check if user has university offer letter
7. **coapplicant_itr_question** - Check co-applicant ITR availability
8. **collateral_question** - Check collateral availability
9. **visa_timeline_question** - Ask about visa timeline
10. **qualification_summary** - Summarize eligibility category
11. **handoff_offer** - Offer to connect with human expert
12. **callback_scheduling** - Schedule callback if user prefers
13. **goodbye** - End call gracefully
14. **clarification** - Handle unclear responses
15. **language_switch** - Confirm language change
16. **consent_request** - Request call recording consent
17. **negative_response** - Handle frustrated users
18. **silence_prompt** - Handle silence/no response

## Setup

### 1. Seed Prompts

Run the seed script to populate the database with initial prompts:

```bash
cd backend
python seed_prompts.py
```

This will insert 54 prompts (18 states × 3 languages) into the database.

### 2. Generate TTS Audio (Optional)

To pre-generate TTS audio for all prompts:

```bash
python generate_tts_cache.py
```

**Prerequisites:**
- Google Cloud TTS: Set `GOOGLE_CLOUD_PROJECT` and configure credentials
- AWS Polly: Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

The script will:
- Generate MP3 audio files for all prompts
- Upload to cloud storage (GCS or S3)
- Update database with audio URLs

### 3. Regenerate Single Prompt

To regenerate audio for a specific prompt:

```bash
python generate_tts_cache.py hinglish_greeting
```

## API Endpoints

### Get Prompts

```http
GET /api/v1/config/prompts?language=hinglish&state=greeting
```

### Create New Prompt Version

```http
POST /api/v1/config/prompts/{state}/{language}/versions
Content-Type: application/json

{
  "text": "New prompt text for A/B testing"
}
```

### Get All Versions

```http
GET /api/v1/config/prompts/{state}/{language}/versions
```

### Rollback to Previous Version

```http
POST /api/v1/config/prompts/{state}/{language}/rollback/{version}
```

### Get Active Prompt

```http
GET /api/v1/config/prompts/{state}/{language}/active
```

### Regenerate Audio

```http
POST /api/v1/config/prompts/{prompt_id}/regenerate-audio
```

### Cache All Prompts

```http
POST /api/v1/config/prompts/cache-all?language=hinglish
```

## Usage in Code

### Get Prompt Text

```python
from app.data.prompts import get_prompt_by_state_and_language

prompt_text = get_prompt_by_state_and_language("greeting", "hinglish")
```

### Get Prompt with Audio URL

```python
from app.repositories.prompt_repository import PromptRepository

prompt_repo = PromptRepository(db)
prompt = await prompt_repo.get_prompt("greeting", "hinglish")

if prompt.audio_url:
    # Use pre-generated audio
    play_audio(prompt.audio_url)
else:
    # Fallback to real-time TTS
    generate_and_play_tts(prompt.text)
```

### Create New Version

```python
new_version = await prompt_repo.create_new_version(
    state="greeting",
    language="hinglish",
    new_text="Namaste! Updated greeting message..."
)
```

### Rollback Version

```python
previous_version = await prompt_repo.rollback_to_version(
    state="greeting",
    language="hinglish",
    version=1
)
```

## Prompt Customization

### Adding New States

1. Add state to `CONVERSATION_STATES` in `app/data/prompts.py`
2. Add prompts for all languages in the respective dictionaries
3. Run `python seed_prompts.py` to update database
4. Optionally run `python generate_tts_cache.py` to generate audio

### Modifying Existing Prompts

**Option 1: Update in Code**
1. Edit prompt text in `app/data/prompts.py`
2. Run `python seed_prompts.py` to update database
3. Run `python generate_tts_cache.py` to regenerate audio

**Option 2: Update via API**
1. Create new version via API endpoint
2. Test the new version
3. Rollback if needed

## A/B Testing

The versioning system supports A/B testing:

1. Create multiple versions of a prompt
2. Manually activate different versions for different user segments
3. Track performance metrics
4. Rollback to best-performing version

## TTS Configuration

### Google Cloud TTS

Voice configurations:
- **Hinglish**: hi-IN-Wavenet-D (Hindi voice)
- **English**: en-US-Wavenet-F (Female US English)
- **Telugu**: te-IN-Standard-A (Telugu voice)

### AWS Polly

Voice configurations:
- **Hinglish**: Aditi (Hindi, Neural)
- **English**: Joanna (US English, Neural)
- **Telugu**: Aditi (fallback to Hindi)

## Database Schema

```javascript
{
  prompt_id: "hinglish_greeting",
  state: "greeting",
  language: "hinglish",
  text: "Namaste! Main aapki education loan advisor hoon...",
  audio_url: "https://storage.googleapis.com/prompts/hinglish_greeting.mp3",
  version: 1,
  is_active: true
}
```

## Best Practices

1. **Always test prompts** before deploying to production
2. **Use versioning** for any prompt changes
3. **Pre-generate audio** for common prompts to reduce latency
4. **Monitor performance** of different prompt versions
5. **Keep prompts concise** (under 30 seconds when spoken)
6. **Use natural language** appropriate for each language
7. **Include fallbacks** for TTS failures

## Troubleshooting

### Prompts not found
- Run `python seed_prompts.py` to ensure prompts are in database
- Check database connection settings

### Audio generation fails
- Verify TTS provider credentials are configured
- Check cloud storage bucket permissions
- Review logs for specific error messages

### Version conflicts
- Use rollback endpoint to revert to known good version
- Check `is_active` flag in database

## Future Enhancements

- Automatic A/B testing with performance tracking
- Dynamic prompt generation based on user context
- Multi-variant testing (more than 2 versions)
- Prompt analytics dashboard
- Voice cloning for brand consistency
