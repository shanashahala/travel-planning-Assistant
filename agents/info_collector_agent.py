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
    
    # Check if package_type has changed to trigger reset
    current_pkg_type = state.get("package_type")
    new_pkg_type = extracted.package_type
    
    if new_pkg_type and current_pkg_type and new_pkg_type.lower() != current_pkg_type.lower():
        logger.info(f"Package type changed from {current_pkg_type} to {new_pkg_type}. Resetting other preferences.")
        # Reset other details as per user request
        updates["destination"] = None
        updates["budget"] = None
        updates["duration_days"] = None
        updates["traveler_type"] = None
        updates["activities"] = []
        updates["research_results"] = []
        updates["ranked_packages"] = []
        updates["selected_package"] = {}
        updates["day_plan"] = []
    
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
    # Only merge if package_type didn't change (if it changed, we reset it above)
    if extracted.activities and len(extracted.activities) > 0:
        if updates.get("activities") == []: # Reset happened
            updates["activities"] = extracted.activities
        else:
            existing_activities = state.get("activities", [])
            merged_activities = list(set(existing_activities + extracted.activities))
            updates["activities"] = merged_activities
        logger.info(f"Updated activities: {updates['activities']}")
    
    # Log results
    if updates:
        logger.info(f"Updated preferences: {updates}")
    else:
        logger.info("No new preferences extracted")
    
    if extracted.notes:
        logger.warning(f"Extraction notes: {extracted.notes}")
    
    # Update state with extracted preferences
    # We use state.update(updates) style to ensure None values actually overwrite
    new_state = state.copy()
    for k, v in updates.items():
        new_state[k] = v
    
    # Compute available_destinations based on package_type
    all_packages = state.get("packages", [])
    if not all_packages:
        logger.info("Packages absent in state. Loading from file.")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        package_file = os.path.join(base_dir, "dataset", "Packages.json")
        try:
            with open(package_file, 'r') as f:
                all_packages = json.load(f)
            new_state["packages"] = all_packages
        except Exception as e:
            logger.error(f"Error loading packages: {e}")
            all_packages = []
            
    final_pkg_type = new_state.get("package_type")
    final_dest = new_state.get("destination")
    
    if final_pkg_type:
        # Get unique destinations for this package_type
        destinations_for_type = sorted(list(set([
            p.get("destination") 
            for p in all_packages 
            if p.get("package_type") and str(p.get("package_type")).lower() == final_pkg_type.lower()
        ])))
        new_state["available_destinations"] = destinations_for_type
        logger.info(f"Available destinations for {final_pkg_type}: {destinations_for_type}")
        
        # Update current_state based on what we have
        if final_dest:
            # We have both package_type and destination -> move to destination_selected
            new_state["current_state"] = "destination_selected"
            logger.info(f"State updated to destination_selected: {final_pkg_type} -> {final_dest}")
        else:
            # Only package_type set -> move to package_type_selected
            new_state["current_state"] = "package_type_selected"
            logger.info(f"State updated to package_type_selected: {final_pkg_type}")
    
    # Add system message if preferences were updated
    if updates:
        summary = ", ".join([f"{k}={v}" for k, v in updates.items()])
        new_state["messages"] = [
            SystemMessage(content=f"[Preferences Updated: {summary}]")
        ]
    
    return new_state