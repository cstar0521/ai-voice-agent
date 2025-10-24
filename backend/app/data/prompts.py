"""
Voice prompt templates for all conversation states in multiple languages.
These prompts are used by the conversation manager to generate TTS audio.
"""

from typing import Dict, List
from app.models.configuration import VoicePrompt

# Conversation states
CONVERSATION_STATES = [
    "greeting",
    "intent_confirmation",
    "degree_question",
    "country_question",
    "loan_amount_question",
    "offer_letter_question",
    "coapplicant_itr_question",
    "collateral_question",
    "visa_timeline_question",
    "qualification_summary",
    "handoff_offer",
    "callback_scheduling",
    "goodbye",
    "clarification",
    "language_switch",
    "consent_request",
    "negative_response",
    "silence_prompt",
]

# Hinglish prompts
HINGLISH_PROMPTS: Dict[str, str] = {
    "greeting": "Namaste! Main aapki education loan advisor hoon. Kya aap videsh mein padhai ke liye loan ke baare mein jaanna chahte hain?",
    
    "intent_confirmation": "Bahut achha! Main aapki madad karunga. Kya aap mujhe bata sakte hain ki aap kis country mein padhai karna chahte hain?",
    
    "degree_question": "Aap kaun si degree pursue karna chahte hain - Bachelors, Masters, ya MBA?",
    
    "country_question": "Aap kis country mein padhai karna chahte hain? Jaise US, UK, Canada, Australia, ya Germany?",
    
    "loan_amount_question": "Aapko kitne rupees ka loan chahiye? Approximate amount bataiye.",
    
    "offer_letter_question": "Kya aapke paas kisi university se offer letter hai?",
    
    "coapplicant_itr_question": "Kya aapke co-applicant ke paas pichle 2 saal ka ITR hai?",
    
    "collateral_question": "Kya aapke paas koi collateral hai jaise property ya fixed deposit?",
    
    "visa_timeline_question": "Aapko visa kab tak chahiye? Kitne mahine baaki hain?",
    
    "qualification_summary": "Dhanyavaad! Aapki details ke hisaab se, aap {category} loan ke liye eligible lag rahe hain. Main aapko ek expert se connect kar sakta hoon jo aapko detailed guidance denge.",
    
    "handoff_offer": "Kya main aapko abhi ek loan expert se connect kar doon? Wo aapko puri process explain karenge.",
    
    "callback_scheduling": "Koi baat nahi. Aap kab baat karna chahenge? Main aapko us time pe call karunga.",
    
    "goodbye": "Dhanyavaad aapka time dene ke liye! Hum jald hi aapse contact karenge. Namaste!",
    
    "clarification": "Maaf kijiye, main samajh nahi paaya. Kya aap phir se bata sakte hain?",
    
    "language_switch": "Main ab {language} mein baat karunga. Kya yeh theek hai?",
    
    "consent_request": "Is call ko recording ke liye aapki permission chahiye. Kya aap allow karte hain?",
    
    "negative_response": "Main samajhta hoon ki aap pareshaan hain. Kya main aapko abhi ek human expert se connect kar doon?",
    
    "silence_prompt": "Kya aap wahan hain? Kya aap continue karna chahte hain ya main baad mein call karoon?",
}

# English prompts
ENGLISH_PROMPTS: Dict[str, str] = {
    "greeting": "Hello! I'm your education loan advisor. Are you interested in learning about loans for studying abroad?",
    
    "intent_confirmation": "Great! I'll help you with that. Can you tell me which country you're planning to study in?",
    
    "degree_question": "Which degree are you planning to pursue - Bachelors, Masters, or MBA?",
    
    "country_question": "Which country are you planning to study in? For example, US, UK, Canada, Australia, or Germany?",
    
    "loan_amount_question": "How much loan amount do you need? Please provide an approximate amount in rupees.",
    
    "offer_letter_question": "Do you have an offer letter from any university?",
    
    "coapplicant_itr_question": "Does your co-applicant have ITR for the last 2 years?",
    
    "collateral_question": "Do you have any collateral such as property or fixed deposit?",
    
    "visa_timeline_question": "When do you need your visa? How many months do you have?",
    
    "qualification_summary": "Thank you! Based on your details, you appear eligible for {category} loan. I can connect you with an expert who will provide detailed guidance.",
    
    "handoff_offer": "Would you like me to connect you with a loan expert right now? They will explain the entire process to you.",
    
    "callback_scheduling": "No problem. When would you like to talk? I'll call you at that time.",
    
    "goodbye": "Thank you for your time! We'll contact you soon. Goodbye!",
    
    "clarification": "I'm sorry, I didn't understand that. Could you please repeat?",
    
    "language_switch": "I'll now speak in {language}. Is that okay?",
    
    "consent_request": "I need your permission to record this call. Do you consent?",
    
    "negative_response": "I understand you're frustrated. Would you like me to connect you with a human expert right now?",
    
    "silence_prompt": "Are you there? Would you like to continue or should I call you back later?",
}

# Telugu prompts
TELUGU_PROMPTS: Dict[str, str] = {
    "greeting": "Namaskaram! Nenu mee education loan advisor ni. Meeru videshallo chaduvukovadaniki loan gurinchi telusukovaalani undi?",
    
    "intent_confirmation": "Chala bagundi! Nenu meeku sahayam chestanu. Meeru ee country lo chaduvukovaalani undi?",
    
    "degree_question": "Meeru ee degree pursue cheyaalani undi - Bachelors, Masters, leda MBA?",
    
    "country_question": "Meeru ee country lo chaduvukovaalani undi? Udaharanaku US, UK, Canada, Australia, leda Germany?",
    
    "loan_amount_question": "Meeku entha loan kavali? Approximate amount cheppandi.",
    
    "offer_letter_question": "Meeku evarayina university nundi offer letter unda?",
    
    "coapplicant_itr_question": "Mee co-applicant ki last 2 years ITR unda?",
    
    "collateral_question": "Meeku evarayina collateral unda like property leda fixed deposit?",
    
    "visa_timeline_question": "Meeku visa eppudu kavali? Enni months unnai?",
    
    "qualification_summary": "Dhanyavadalu! Mee details prakaram, meeru {category} loan ki eligible ga unnaru. Nenu meeku oka expert tho connect cheyagalanu, vaaru detailed guidance istaru.",
    
    "handoff_offer": "Nenu meeku ippudu oka loan expert tho connect cheyamantara? Vaaru mee process antha explain chestaru.",
    
    "callback_scheduling": "Parledu. Meeru eppudu matladaalani undi? Nenu aa time ki meeku call chestanu.",
    
    "goodbye": "Mee time ki dhanyavadalu! Memu tondarga meeku contact chestamu. Namaskaram!",
    
    "clarification": "Kshaminchand, naku artham kaaledu. Meeru malli cheppagalara?",
    
    "language_switch": "Nenu ippudu {language} lo matladutanu. Okay na?",
    
    "consent_request": "Ee call ni record cheyadaniki mee permission kavali. Meeru allow chestara?",
    
    "negative_response": "Nenu artham chesukuntunnanu meeru frustrated ga unnaru. Nenu meeku ippudu human expert tho connect cheyamantara?",
    
    "silence_prompt": "Meeru akkada unnara? Meeru continue cheyaalani unda leda nenu tarvata call cheyamantara?",
}


def get_all_prompts() -> List[VoicePrompt]:
    """
    Generate all voice prompts for all languages and states.
    Returns a list of VoicePrompt objects ready to be inserted into the database.
    """
    prompts = []
    
    # Generate Hinglish prompts
    for state, text in HINGLISH_PROMPTS.items():
        prompts.append(VoicePrompt(
            prompt_id=f"hinglish_{state}",
            state=state,
            language="hinglish",
            text=text,
            audio_url=None,  # Will be populated by TTS caching
            version=1,
            is_active=True,
        ))
    
    # Generate English prompts
    for state, text in ENGLISH_PROMPTS.items():
        prompts.append(VoicePrompt(
            prompt_id=f"english_{state}",
            state=state,
            language="english",
            text=text,
            audio_url=None,
            version=1,
            is_active=True,
        ))
    
    # Generate Telugu prompts
    for state, text in TELUGU_PROMPTS.items():
        prompts.append(VoicePrompt(
            prompt_id=f"telugu_{state}",
            state=state,
            language="telugu",
            text=text,
            audio_url=None,
            version=1,
            is_active=True,
        ))
    
    return prompts


def get_prompt_by_state_and_language(state: str, language: str) -> str:
    """
    Get a prompt text for a specific state and language.
    """
    language_prompts = {
        "hinglish": HINGLISH_PROMPTS,
        "english": ENGLISH_PROMPTS,
        "telugu": TELUGU_PROMPTS,
    }
    
    prompts = language_prompts.get(language.lower())
    if not prompts:
        # Fallback to English
        prompts = ENGLISH_PROMPTS
    
    return prompts.get(state, "")
