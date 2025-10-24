"""
Conversation State Machine for managing dialogue flow.
"""
from enum import Enum
from typing import Dict, List, Optional, Set
from datetime import datetime


class ConversationState(str, Enum):
    """
    Enumeration of all possible conversation states.
    
    The state machine follows this general flow:
    INITIATED -> GREETING -> LANGUAGE_DETECTION -> QUALIFICATION_START
    -> (collect data) -> ELIGIBILITY_MAPPING -> HANDOFF_OFFER
    -> (handoff or followup) -> ENDING -> COMPLETED
    """
    # Initial states
    INITIATED = "initiated"
    GREETING = "greeting"
    LANGUAGE_DETECTION = "language_detection"
    
    # Qualification states
    QUALIFICATION_START = "qualification_start"
    COLLECT_DEGREE = "collect_degree"
    COLLECT_COUNTRY = "collect_country"
    COLLECT_OFFER_LETTER = "collect_offer_letter"
    COLLECT_LOAN_AMOUNT = "collect_loan_amount"
    COLLECT_ITR = "collect_itr"
    COLLECT_COLLATERAL = "collect_collateral"
    COLLECT_VISA_TIMELINE = "collect_visa_timeline"
    
    # Processing states
    ELIGIBILITY_MAPPING = "eligibility_mapping"
    LENDER_RECOMMENDATION = "lender_recommendation"
    
    # Handoff states
    HANDOFF_OFFER = "handoff_offer"
    HANDOFF_ACCEPTED = "handoff_accepted"
    HANDOFF_DECLINED = "handoff_declined"
    TRANSFERRING = "transferring"
    TRANSFERRED = "transferred"
    
    # Followup states
    FOLLOWUP_SCHEDULED = "followup_scheduled"
    CALLBACK_SCHEDULED = "callback_scheduled"
    
    # Terminal states
    ENDING = "ending"
    COMPLETED = "completed"
    
    # Error states
    FAILED = "failed"
    NO_ANSWER = "no_answer"
    USER_HANGUP = "user_hangup"
    NETWORK_ERROR = "network_error"
    ESCALATED = "escalated"


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class ConversationStateMachine:
    """
    State machine for managing conversation flow and transitions.
    
    This class defines valid state transitions and provides methods
    to transition between states with validation.
    """
    
    # Define valid state transitions
    VALID_TRANSITIONS: Dict[ConversationState, Set[ConversationState]] = {
        ConversationState.INITIATED: {
            ConversationState.GREETING,
            ConversationState.FAILED,
            ConversationState.NO_ANSWER
        },
        ConversationState.GREETING: {
            ConversationState.LANGUAGE_DETECTION,
            ConversationState.QUALIFICATION_START,  # Skip language detection if already known
            ConversationState.USER_HANGUP,
            ConversationState.NETWORK_ERROR
        },
        ConversationState.LANGUAGE_DETECTION: {
            ConversationState.QUALIFICATION_START,
            ConversationState.USER_HANGUP,
            ConversationState.NETWORK_ERROR
        },
        ConversationState.QUALIFICATION_START: {
            ConversationState.COLLECT_DEGREE,
            ConversationState.HANDOFF_OFFER,  # User requests handoff immediately
            ConversationState.USER_HANGUP,
            ConversationState.NETWORK_ERROR
        },
        ConversationState.COLLECT_DEGREE: {
            ConversationState.COLLECT_COUNTRY,
            ConversationState.HANDOFF_OFFER,
            ConversationState.ESCALATED,
            ConversationState.USER_HANGUP,
            ConversationState.NETWORK_ERROR
        },
        ConversationState.COLLECT_COUNTRY: {
            ConversationState.COLLECT_OFFER_LETTER,
            ConversationState.HANDOFF_OFFER,
            ConversationState.ESCALATED,
            ConversationState.USER_HANGUP,
            ConversationState.NETWORK_ERROR
        },
        ConversationState.COLLECT_OFFER_LETTER: {
            ConversationState.COLLECT_LOAN_AMOUNT,
            ConversationState.HANDOFF_OFFER,
            ConversationState.ESCALATED,
            ConversationState.USER_HANGUP,
            ConversationState.NETWORK_ERROR
        },
        ConversationState.COLLECT_LOAN_AMOUNT: {
            ConversationState.COLLECT_ITR,
            ConversationState.HANDOFF_OFFER,
            ConversationState.ESCALATED,
            ConversationState.USER_HANGUP,
            ConversationState.NETWORK_ERROR
        },
        ConversationState.COLLECT_ITR: {
            ConversationState.COLLECT_COLLATERAL,
            ConversationState.HANDOFF_OFFER,
            ConversationState.ESCALATED,
            ConversationState.USER_HANGUP,
            ConversationState.NETWORK_ERROR
        },
        ConversationState.COLLECT_COLLATERAL: {
            ConversationState.COLLECT_VISA_TIMELINE,
            ConversationState.HANDOFF_OFFER,
            ConversationState.ESCALATED,
            ConversationState.USER_HANGUP,
            ConversationState.NETWORK_ERROR
        },
        ConversationState.COLLECT_VISA_TIMELINE: {
            ConversationState.ELIGIBILITY_MAPPING,
            ConversationState.HANDOFF_OFFER,
            ConversationState.ESCALATED,
            ConversationState.USER_HANGUP,
            ConversationState.NETWORK_ERROR
        },
        ConversationState.ELIGIBILITY_MAPPING: {
            ConversationState.LENDER_RECOMMENDATION,
            ConversationState.HANDOFF_OFFER,
            ConversationState.ESCALATED,
            ConversationState.USER_HANGUP,
            ConversationState.NETWORK_ERROR
        },
        ConversationState.LENDER_RECOMMENDATION: {
            ConversationState.HANDOFF_OFFER,
            ConversationState.ENDING,
            ConversationState.USER_HANGUP,
            ConversationState.NETWORK_ERROR
        },
        ConversationState.HANDOFF_OFFER: {
            ConversationState.HANDOFF_ACCEPTED,
            ConversationState.HANDOFF_DECLINED,
            ConversationState.USER_HANGUP,
            ConversationState.NETWORK_ERROR
        },
        ConversationState.HANDOFF_ACCEPTED: {
            ConversationState.TRANSFERRING,
            ConversationState.CALLBACK_SCHEDULED,  # No expert available
            ConversationState.USER_HANGUP,
            ConversationState.NETWORK_ERROR
        },
        ConversationState.HANDOFF_DECLINED: {
            ConversationState.FOLLOWUP_SCHEDULED,
            ConversationState.ENDING,
            ConversationState.USER_HANGUP,
            ConversationState.NETWORK_ERROR
        },
        ConversationState.TRANSFERRING: {
            ConversationState.TRANSFERRED,
            ConversationState.FAILED,
            ConversationState.USER_HANGUP,
            ConversationState.NETWORK_ERROR
        },
        ConversationState.TRANSFERRED: {
            ConversationState.COMPLETED
        },
        ConversationState.FOLLOWUP_SCHEDULED: {
            ConversationState.ENDING,
            ConversationState.USER_HANGUP,
            ConversationState.NETWORK_ERROR
        },
        ConversationState.CALLBACK_SCHEDULED: {
            ConversationState.ENDING,
            ConversationState.USER_HANGUP,
            ConversationState.NETWORK_ERROR
        },
        ConversationState.ENDING: {
            ConversationState.COMPLETED
        },
        ConversationState.ESCALATED: {
            ConversationState.HANDOFF_OFFER,
            ConversationState.ENDING
        },
        # Terminal states have no outgoing transitions
        ConversationState.COMPLETED: set(),
        ConversationState.FAILED: set(),
        ConversationState.NO_ANSWER: set(),
        ConversationState.USER_HANGUP: set(),
        ConversationState.NETWORK_ERROR: set()
    }
    
    # Terminal states that end the conversation
    TERMINAL_STATES: Set[ConversationState] = {
        ConversationState.COMPLETED,
        ConversationState.FAILED,
        ConversationState.NO_ANSWER,
        ConversationState.USER_HANGUP,
        ConversationState.NETWORK_ERROR
    }
    
    # States that require data collection
    DATA_COLLECTION_STATES: Set[ConversationState] = {
        ConversationState.COLLECT_DEGREE,
        ConversationState.COLLECT_COUNTRY,
        ConversationState.COLLECT_OFFER_LETTER,
        ConversationState.COLLECT_LOAN_AMOUNT,
        ConversationState.COLLECT_ITR,
        ConversationState.COLLECT_COLLATERAL,
        ConversationState.COLLECT_VISA_TIMELINE
    }
    
    def __init__(self, initial_state: ConversationState = ConversationState.INITIATED):
        """
        Initialize state machine with an initial state.
        
        Args:
            initial_state: Starting state for the conversation
        """
        self.current_state = initial_state
        self.state_history: List[Dict] = [{
            "state": initial_state,
            "timestamp": datetime.utcnow(),
            "reason": "initialization"
        }]
    
    def can_transition_to(self, target_state: ConversationState) -> bool:
        """
        Check if transition to target state is valid from current state.
        
        Args:
            target_state: State to transition to
        
        Returns:
            True if transition is valid, False otherwise
        """
        valid_targets = self.VALID_TRANSITIONS.get(self.current_state, set())
        return target_state in valid_targets
    
    def transition_to(
        self,
        target_state: ConversationState,
        reason: Optional[str] = None
    ) -> None:
        """
        Transition to a new state with validation.
        
        Args:
            target_state: State to transition to
            reason: Optional reason for the transition
        
        Raises:
            StateTransitionError: If transition is invalid
        """
        if not self.can_transition_to(target_state):
            raise StateTransitionError(
                f"Invalid transition from {self.current_state} to {target_state}"
            )
        
        # Record transition in history
        self.state_history.append({
            "from_state": self.current_state,
            "to_state": target_state,
            "timestamp": datetime.utcnow(),
            "reason": reason or "state_transition"
        })
        
        self.current_state = target_state
    
    def is_terminal(self) -> bool:
        """
        Check if current state is a terminal state.
        
        Returns:
            True if current state is terminal, False otherwise
        """
        return self.current_state in self.TERMINAL_STATES
    
    def is_data_collection(self) -> bool:
        """
        Check if current state is a data collection state.
        
        Returns:
            True if current state requires data collection, False otherwise
        """
        return self.current_state in self.DATA_COLLECTION_STATES
    
    def get_next_collection_state(self) -> Optional[ConversationState]:
        """
        Get the next data collection state in sequence.
        
        Returns:
            Next collection state, or None if current state is not a collection state
        """
        collection_sequence = [
            ConversationState.COLLECT_DEGREE,
            ConversationState.COLLECT_COUNTRY,
            ConversationState.COLLECT_OFFER_LETTER,
            ConversationState.COLLECT_LOAN_AMOUNT,
            ConversationState.COLLECT_ITR,
            ConversationState.COLLECT_COLLATERAL,
            ConversationState.COLLECT_VISA_TIMELINE
        ]
        
        try:
            current_index = collection_sequence.index(self.current_state)
            if current_index < len(collection_sequence) - 1:
                return collection_sequence[current_index + 1]
            else:
                # Last collection state, move to eligibility mapping
                return ConversationState.ELIGIBILITY_MAPPING
        except ValueError:
            # Current state is not in collection sequence
            return None
    
    def get_state_history(self) -> List[Dict]:
        """
        Get the history of state transitions.
        
        Returns:
            List of state transition records
        """
        return self.state_history.copy()
    
    def reset(self, initial_state: ConversationState = ConversationState.INITIATED) -> None:
        """
        Reset the state machine to initial state.
        
        Args:
            initial_state: State to reset to
        """
        self.current_state = initial_state
        self.state_history = [{
            "state": initial_state,
            "timestamp": datetime.utcnow(),
            "reason": "reset"
        }]
