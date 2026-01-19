import os
import json
import logging
from typing import Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv

from graphs.state import AgentState
from prompts.info_collector_prompt import get_info_collector_prompt
from models import ExtractedPreferences

load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

# Initialize LLM and chain (module-level, loaded once)
logger.info("Initializing InfoCollectorAgent")
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set")
logger.info("Groq API key loaded successfully")

_llm = ChatGroq(
    groq_api_key=groq_api_key,
    model="llama-3.3-70b-versatile",
    temperature=0.1,
)

_structured_llm = _llm.with_structured_output(ExtractedPreferences)

_prompt = ChatPromptTemplate.from_messages([
    ("system", get_info_collector_prompt()),
    ("human", "{input}")
])

_chain = _prompt | _structured_llm


def _build_context(state: AgentState) -> str:
    """Build extraction context from state"""
    existing = {
        "package_type": state.get("package_type"),
        "destination": state.get("destination"),
        "budget": state.get("budget"),
        "duration_days": state.get("duration_days"),
        "traveler_type": state.get("traveler_type"),
        "activities": state.get("activities", [])  # ⭐ INCLUDE ACTIVITIES
    }
    
    # Get last 3 messages for context
    recent_msgs = []
    for msg in state.get("messages", [])[-3:]:
        if isinstance(msg, HumanMessage):
            recent_msgs.append(f"User: {msg.content}")
        elif isinstance(msg, AIMessage):
            recent_msgs.append(f"Assistant: {msg.content}")
    
    context = f"""Current Preferences:
{json.dumps(existing, indent=2)}

Recent Messages:
{chr(10).join(recent_msgs)}

Extract any NEW or UPDATED preferences from the latest user message."""
    
    return context


def _extract_preferences(state: AgentState) -> ExtractedPreferences:
    """Extract preferences from conversation"""
    context = _build_context(state)
    
    try:
        extracted = _chain.invoke({"input": context})
        logger.info(f"Extraction successful - Confidence: {extracted.confidence}")
        return extracted
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return ExtractedPreferences(
            confidence="low",
            notes=f"Extraction error: {str(e)}"
        )


def info_collector_agent(state: AgentState) -> AgentState:
    """
    Info Collector Agent - Extracts and updates user preferences from conversation.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with extracted preferences
    """
    logger.info("InfoCollectorAgent invoked")
    
    extracted = _extract_preferences(state)
    
    # ⭐ DEBUG LOG - See what was extracted
    logger.info(f"Extracted activities: {extracted.activities}")
    
    # Build updates dict (only non-null values)
    updates = {}
    
    if extracted.package_type is not None:
        updates["package_type"] = extracted.package_type
        
    if extracted.destination is not None:
        updates["destination"] = extracted.destination
        
    if extracted.budget is not None:
        updates["budget"] = float(extracted.budget)
        
    if extracted.duration_days is not None:
        updates["duration_days"] = int(extracted.duration_days)
        
    if extracted.traveler_type is not None:
        updates["traveler_type"] = extracted.traveler_type
    
    # ⭐ HANDLE ACTIVITIES - Merge with existing (avoid duplicates)
    if extracted.activities and len(extracted.activities) > 0:
        existing_activities = state.get("activities", [])
        # Merge and remove duplicates
        merged_activities = list(set(existing_activities + extracted.activities))
        updates["activities"] = merged_activities
        logger.info(f"Merged activities: {merged_activities}")
    
    # Log results
    if updates:
        logger.info(f"Updated preferences: {updates}")
    else:
        logger.info("No new preferences extracted")
    
    if extracted.notes:
        logger.warning(f"Extraction notes: {extracted.notes}")
    
    # Update state with extracted preferences
    new_state = {**state, **updates}
    
    # Add system message if preferences were updated
    if updates:
        summary = ", ".join([f"{k}={v}" for k, v in updates.items()])
        new_state["messages"] = [
            SystemMessage(content=f"[Preferences Updated: {summary}]")
        ]
    
    return new_state