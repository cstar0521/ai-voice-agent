"""
Prompt Generator for creating context-aware voice prompts in multiple languages.
"""
from typing import Dict, Optional, Any
from app.services.conversation_state_machine import ConversationState
from app.services.conversation_context import ConversationContext


class PromptGenerator:
    """
    Generates voice prompts based on conversation state, language, and context.
    
    Supports three languages: Hinglish, English, and Telugu.
    """
    
    # Prompt templates for each state and language
    PROMPTS: Dict[ConversationState, Dict[str, str]] = {
        ConversationState.GREETING: {
            "hinglish": "Namaste! Main EduLoan ki AI assistant hoon. Kya aap study abroad ke liye education loan ke baare mein jaanna chahte hain?",
            "english": "Hello! I'm an AI assistant from EduLoan. Are you interested in learning about education loans for studying abroad?",
            "telugu": "Namaskaram! Nenu EduLoan AI assistant ni. Miru videshallo chaduvukovadaniki education loan gurinchi telusukovaalani undi?"
        },
        ConversationState.LANGUAGE_DETECTION: {
            "hinglish": "Main aapko Hindi, English, ya Telugu mein help kar sakti hoon. Aap kis language mein baat karna pasand karenge?",
            "english": "I can help you in Hindi, English, or Telugu. Which language would you prefer?",
            "telugu": "Nenu mimmalini Hindi, English, leda Telugu lo sahayam cheyagalanu. Meeku e bhasha nachutundi?"
        },
        ConversationState.QUALIFICATION_START: {
            "hinglish": "Bahut achha! Main aapki eligibility check karne ke liye kuch basic questions poochungi. Isme sirf 2-3 minute lagenge. Chalein?",
            "english": "Great! I'll ask you a few basic questions to check your eligibility. This will only take 2-3 minutes. Shall we begin?",
            "telugu": "Chala bagundi! Mee eligibility check cheyadaniki nenu konni basic prashnalu adugutanu. Idi 2-3 nimishalu matrame teesukuntundi. Modalu pedatama?"
        },
        ConversationState.COLLECT_DEGREE: {
            "hinglish": "Aap kaun sa degree pursue karna chahte hain? Bachelors, Masters, ya MBA?",
            "english": "Which degree are you planning to pursue? Bachelors, Masters, or MBA?",
            "telugu": "Meeru e degree pursue cheyyalani undi? Bachelors, Masters, leda MBA?"
        },
        ConversationState.COLLECT_COUNTRY: {
            "hinglish": "Aap kis country mein padhai karna chahte hain? Jaise US, UK, Canada, Australia, ya koi aur?",
            "english": "Which country are you planning to study in? For example, US, UK, Canada, Australia, or another country?",
            "telugu": "Meeru e deshallo chaduvukovaalani undi? Udaharanaku US, UK, Canada, Australia, leda vere desham?"
        },
        ConversationState.COLLECT_OFFER_LETTER: {
            "hinglish": "Kya aapko university se offer letter mil gaya hai?",
            "english": "Have you received an offer letter from the university?",
            "telugu": "Meeku university nundi offer letter vachinda?"
        },
        ConversationState.COLLECT_LOAN_AMOUNT: {
            "hinglish": "Aapko kitne rupees ka loan chahiye? Approximate amount bataiye.",
            "english": "How much loan amount do you need? Please provide an approximate amount in rupees.",
            "telugu": "Meeku entha loan kavali? Approximate amount rupees lo cheppandi."
        },
        ConversationState.COLLECT_ITR: {
            "hinglish": "Kya aapke co-applicant, matlab parents ya guardian, ka Income Tax Return file hai?",
            "english": "Does your co-applicant, meaning your parents or guardian, have an Income Tax Return filed?",
            "telugu": "Mee co-applicant, ante mee parents leda guardian, Income Tax Return file chesara?"
        },
        ConversationState.COLLECT_COLLATERAL: {
            "hinglish": "Kya aapke paas collateral hai? Matlab property ya koi asset jo aap loan ke liye pledge kar sakte hain?",
            "english": "Do you have collateral? That means property or any asset that you can pledge for the loan?",
            "telugu": "Meeku collateral unda? Ante property leda emi asset loan kosam pledge cheyagalaru?"
        },
        ConversationState.COLLECT_VISA_TIMELINE: {
            "hinglish": "Aapko visa kab tak chahiye? Kitne din ya mahine mein?",
            "english": "When do you need your visa? In how many days or months?",
            "telugu": "Meeku visa eppudu kavali? Enni rojulu leda nelalu lo?"
        },
        ConversationState.ELIGIBILITY_MAPPING: {
            "hinglish": "Ek minute dijiye, main aapki eligibility check kar rahi hoon...",
            "english": "One moment please, I'm checking your eligibility...",
            "telugu": "Oka nimisham ivvandi, nenu mee eligibility check chestunnanu..."
        },
        ConversationState.LENDER_RECOMMENDATION: {
            "hinglish": "Aapki profile ke basis par, main aapko kuch lenders recommend kar sakti hoon.",
            "english": "Based on your profile, I can recommend some lenders for you.",
            "telugu": "Mee profile batti, nenu meeku konni lenders recommend cheyagalanu."
        },
        ConversationState.HANDOFF_OFFER: {
            "hinglish": "Kya aap hamare loan expert se baat karna chahenge? Wo aapko detailed guidance de sakte hain.",
            "english": "Would you like to speak with our loan expert? They can provide you with detailed guidance.",
            "telugu": "Meeru maa loan expert tho matladali anukuntuunnara? Varu meeku detailed guidance ivvagalaru."
        },
        ConversationState.HANDOFF_ACCEPTED: {
            "hinglish": "Bilkul! Main aapko expert se connect kar rahi hoon. Thoda wait kijiye.",
            "english": "Absolutely! I'm connecting you to an expert. Please wait a moment.",
            "telugu": "Avunu! Nenu mimmalini expert tho connect chestunnanu. Konchem wait cheyandi."
        },
        ConversationState.HANDOFF_DECLINED: {
            "hinglish": "Koi baat nahi! Main aapko WhatsApp par ek summary bhej dungi with next steps.",
            "english": "No problem! I'll send you a summary on WhatsApp with the next steps.",
            "telugu": "Parledu! Nenu meeku WhatsApp lo oka summary pampistanu next steps tho."
        },
        ConversationState.CALLBACK_SCHEDULED: {
            "hinglish": "Abhi koi expert available nahi hai. Kya main aapke liye callback schedule kar doon?",
            "english": "No expert is available right now. Shall I schedule a callback for you?",
            "telugu": "Ippudu evaru expert available ledu. Nenu meeku callback schedule cheyamantara?"
        },
        ConversationState.ENDING: {
            "hinglish": "Aapka bahut bahut dhanyavaad! Aapko jald hi humari team se call aayega. Have a great day!",
            "english": "Thank you so much! Our team will call you soon. Have a great day!",
            "telugu": "Chala dhanyavadalu! Maa team meeku tondarga call chestaru. Have a great day!"
        },
        ConversationState.ESCALATED: {
            "hinglish": "Main samajh sakti hoon ki yeh thoda confusing ho sakta hai. Chaliye main aapko expert se connect karti hoon.",
            "english": "I understand this might be a bit confusing. Let me connect you with an expert.",
            "telugu": "Idi konchem confusing ga undavachu ani naku artham aindi. Nenu mimmalini expert tho connect chestanu."
        }
    }
    
    # Clarification prompts
    CLARIFICATION_PROMPTS: Dict[str, str] = {
        "hinglish": "Sorry, main aapka response clearly samajh nahi payi. Kya aap phir se bata sakte hain?",
        "english": "Sorry, I didn't quite understand your response. Could you please repeat that?",
        "telugu": "Sorry, nenu mee response clear ga artham chesukoలేకపోయాను. Meeru malli cheppagalara?"
    }
    
    # Silence timeout prompts
    SILENCE_PROMPTS: Dict[str, str] = {
        "hinglish": "Kya aap wahan hain? Agar aap chahein toh hum baad mein baat kar sakte hain.",
        "english": "Are you still there? If you'd like, we can talk later.",
        "telugu": "Meeru akkada unnara? Meeku kavali ante mana tarvata matladukovalemo."
    }
    
    # Negative sentiment response prompts
    NEGATIVE_SENTIMENT_PROMPTS: Dict[str, str] = {
        "hinglish": "Main samajh sakti hoon ki aap frustrated feel kar rahe hain. Kya main aapko expert se connect kar doon?",
        "english": "I understand you might be feeling frustrated. Would you like me to connect you with an expert?",
        "telugu": "Meeru frustrated ga feel avutunnaru ani naku artham aindi. Nenu mimmalini expert tho connect cheyamantara?"
    }
    
    def __init__(self):
        """Initialize the prompt generator."""
        pass
    
    def generate_prompt(
        self,
        state: ConversationState,
        language: str,
        context: Optional[ConversationContext] = None
    ) -> str:
        """
        Generate a prompt for the given state and language.
        
        Args:
            state: Current conversation state
            language: Language code (hinglish, english, telugu)
            context: Optional conversation context for personalization
        
        Returns:
            Generated prompt string
        """
        # Get base prompt for state and language
        state_prompts = self.PROMPTS.get(state, {})
        prompt = state_prompts.get(language, state_prompts.get("english", ""))
        
        # Personalize prompt based on context if available
        if context and prompt:
            prompt = self._personalize_prompt(prompt, state, context)
        
        return prompt
    
    def _personalize_prompt(
        self,
        prompt: str,
        state: ConversationState,
        context: ConversationContext
    ) -> str:
        """
        Personalize prompt based on conversation context.
        
        Args:
            prompt: Base prompt string
            state: Current conversation state
            context: Conversation context
        
        Returns:
            Personalized prompt
        """
        # Add lender recommendations for lender recommendation state
        if state == ConversationState.LENDER_RECOMMENDATION:
            lenders = context.get_collected_data("recommended_lenders")
            if lenders and isinstance(lenders, list):
                lender_list = ", ".join(lenders[:3])  # Top 3 lenders
                if context.language == "hinglish":
                    prompt += f" Aapke liye best options hain: {lender_list}."
                elif context.language == "english":
                    prompt += f" The best options for you are: {lender_list}."
                elif context.language == "telugu":
                    prompt += f" Meeku best options: {lender_list}."
        
        return prompt
    
    def generate_clarification_prompt(self, language: str) -> str:
        """
        Generate a clarification prompt.
        
        Args:
            language: Language code
        
        Returns:
            Clarification prompt
        """
        return self.CLARIFICATION_PROMPTS.get(language, self.CLARIFICATION_PROMPTS["english"])
    
    def generate_silence_prompt(self, language: str) -> str:
        """
        Generate a silence timeout prompt.
        
        Args:
            language: Language code
        
        Returns:
            Silence prompt
        """
        return self.SILENCE_PROMPTS.get(language, self.SILENCE_PROMPTS["english"])
    
    def generate_negative_sentiment_prompt(self, language: str) -> str:
        """
        Generate a negative sentiment response prompt.
        
        Args:
            language: Language code
        
        Returns:
            Negative sentiment prompt
        """
        return self.NEGATIVE_SENTIMENT_PROMPTS.get(language, self.NEGATIVE_SENTIMENT_PROMPTS["english"])
    
    def generate_language_switch_confirmation(
        self,
        new_language: str,
        current_language: str
    ) -> str:
        """
        Generate a confirmation prompt for language switch.
        
        Args:
            new_language: Target language
            current_language: Current language
        
        Returns:
            Language switch confirmation prompt
        """
        confirmations = {
            "hinglish": {
                "hinglish": "Haan, main Hinglish mein baat kar rahi hoon.",
                "english": "Sure, I'm switching to English.",
                "telugu": "Haan, main Telugu mein baat karungi."
            },
            "english": {
                "hinglish": "Sure, I'll switch to Hinglish.",
                "english": "I'm already speaking in English.",
                "telugu": "Sure, I'll switch to Telugu."
            },
            "telugu": {
                "hinglish": "Avunu, nenu Hinglish lo matladutanu.",
                "english": "Avunu, nenu English lo matladutanu.",
                "telugu": "Nenu Telugu lo matladutunnanu."
            }
        }
        
        return confirmations.get(current_language, {}).get(
            new_language,
            "Switching language..."
        )
    
    def generate_data_confirmation(
        self,
        field: str,
        value: Any,
        language: str
    ) -> str:
        """
        Generate a confirmation prompt for collected data.
        
        Args:
            field: Field name that was collected
            value: Value that was collected
            language: Language code
        
        Returns:
            Confirmation prompt
        """
        confirmations = {
            "hinglish": {
                "degree": f"Theek hai, toh aap {value} karna chahte hain.",
                "country": f"Samajh gayi, aap {value} mein padhai karenge.",
                "offer_letter": f"Achha, offer letter {'mil gaya hai' if value == 'yes' else 'abhi nahi mila'}.",
                "loan_amount": f"Theek hai, aapko {value} rupees ka loan chahiye.",
                "coapplicant_itr": f"Samajh gayi, ITR {'available hai' if value == 'yes' else 'available nahi hai'}.",
                "collateral": f"Theek hai, collateral {'available hai' if value == 'yes' else 'available nahi hai'}.",
                "visa_timeline": f"Achha, aapko {value} mein visa chahiye."
            },
            "english": {
                "degree": f"Okay, so you want to pursue {value}.",
                "country": f"Got it, you'll be studying in {value}.",
                "offer_letter": f"""Alright, you {'have' if value == 'yes' else "don't have"} an offer letter.""",
                "loan_amount": f"Okay, you need a loan of {value} rupees.",
                "coapplicant_itr": f"Understood, ITR is {'available' if value == 'yes' else 'not available'}.",
                "collateral": f"Okay, collateral is {'available' if value == 'yes' else 'not available'}.",
                "visa_timeline": f"Got it, you need the visa in {value}."
            },
            "telugu": {
                "degree": f"Sare, meeru {value} cheyyalani undi.",
                "country": f"Artham aindi, meeru {value} lo chaduvukuntaru.",
                "offer_letter": f"Sare, offer letter {'vachindi' if value == 'yes' else 'raaledu'}.",
                "loan_amount": f"Sare, meeku {value} rupees loan kavali.",
                "coapplicant_itr": f"Artham aindi, ITR {'available undi' if value == 'yes' else 'available ledu'}.",
                "collateral": f"Sare, collateral {'available undi' if value == 'yes' else 'available ledu'}.",
                "visa_timeline": f"Artham aindi, meeku {value} lo visa kavali."
            }
        }
        
        lang_confirmations = confirmations.get(language, confirmations["english"])
        return lang_confirmations.get(field, f"Okay, {field}: {value}")
