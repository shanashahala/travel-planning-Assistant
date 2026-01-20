from typing import Literal, Dict, Any, Optional
from langgraph.graph import StateGraph, END, START
import logging
from graphs.state import AgentState

# Import agent functions
from agents.conversation_agent import conversation_agent
from agents.info_collector_agent import info_collector_agent
from agents.researcher_agent import researcher_agent
from agents.ranking_agent import ranking_agent
from agents.day_planner_agent import day_planner_agent

# Setup logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Routing Logic

def route_after_conversation(state: AgentState) -> Literal["info_collector", "day_planner", "ranking_agent", "end"]:
    """
    Determines where to go after the conversation manager speaks.
    """
    current_state = state.get("current_state")
    package_confirmed = state.get("package_confirmed")
    available_destinations = state.get("available_destinations", [])
    
    logger.info(f"[Router] After Conversation: State={current_state}, Confirmed={package_confirmed}, Destinations={len(available_destinations)}")

    # User confirmed a package -> Generate day plan
    if current_state == "show_packages" and package_confirmed is True:
        logger.info("[Router] Package confirmed! Routing to Day Planner.")
        return "day_planner"
    
    # User rejected a package -> Get next ranked package
    if current_state == "show_packages" and package_confirmed is False:
        logger.info("[Router] Package rejected. Routing back to Ranking Agent for next option.")
        return "ranking_agent"

    # User wants alternative activities in their plan
    if current_state == "alternative_plan":
        logger.info("[Router] User requested alternative plan. Routing to Day Planner.")
        return "day_planner"

    # Greeting - need to collect package_type
    if current_state == "greeting":
        logger.info("[Router] Greeting state. Routing to Info Collector.")
        return "info_collector"
    
    # Package type selected - check if destinations are already computed
    if current_state == "package_type_selected":
        if available_destinations:
            # Destinations already computed, wait for user to select one
            logger.info("[Router] Package type selected, destinations available. Waiting for user to select destination.")
            return "end"
        else:
            # Need to compute destinations
            logger.info("[Router] Package type selected, need to compute destinations. Routing to Info Collector.")
            return "info_collector"
    
    # Destination selected - need to search packages
    if current_state == "destination_selected":
        logger.info("[Router] Destination selected. Routing to Info Collector for package search.")
        return "info_collector"
    
    # Info gathering - user providing additional preferences
    if current_state == "info_gathering":
        logger.info("[Router] Info gathering. Routing to Info Collector.")
        return "info_collector"

    # Default: End turn and wait for next user input
    logger.info(f"[Router] State '{current_state}' ends turn. Waiting for user input.")
    return "end"


def route_after_info_collector(state: AgentState) -> Literal["researcher_agent", "conversation_agent", "end"]:
    """
    Decides if we have enough info to search or if we need to wait for more user input.
    """
    package_type = state.get("package_type")
    destination = state.get("destination")
    current_state = state.get("current_state")
    
    logger.info(f"[Router] After Info Collector: Type={package_type}, Dest={destination}, State={current_state}")
    
    # If we have both package_type AND destination -> search for packages
    if package_type and destination:
        logger.info("[Router] Primary info (Type & Dest) present. Routing to Researcher.")
        return "researcher_agent"
    
    # If only package_type is set -> Go back to conversation_agent to show destinations
    if package_type and not destination:
        logger.info("[Router] Only package_type set. Routing to Conversation Agent to show destinations.")
        return "conversation_agent"
    
    # Otherwise, end turn to let conversation agent ask for more info
    logger.info("[Router] Info still missing. Ending turn to wait for user input.")
    return "end"


# Graph Construction
def create_travel_workflow():
    workflow = StateGraph(AgentState)

    # Add agent nodes
    workflow.add_node("conversation_agent", conversation_agent)
    workflow.add_node("info_collector", info_collector_agent)
    workflow.add_node("researcher_agent", researcher_agent)
    workflow.add_node("ranking_agent", ranking_agent)
    workflow.add_node("day_planner", day_planner_agent)
      
    # Define the flow
    workflow.add_edge(START, "conversation_agent")

    # From Conversation Agent
    workflow.add_conditional_edges(
        "conversation_agent",
        route_after_conversation,
        {
            "info_collector": "info_collector",
            "day_planner": "day_planner",
            "ranking_agent": "ranking_agent",
            "end": END
        }
    )

    # From Info Collector
    workflow.add_conditional_edges(
        "info_collector",
        route_after_info_collector,
        {
            "researcher_agent": "researcher_agent",
            "conversation_agent": "conversation_agent",
            "end": END
        }
    )

    # Sequential flows
    workflow.add_edge("researcher_agent", "ranking_agent")
    workflow.add_edge("ranking_agent", "conversation_agent")  # Present ranked packages to user
    workflow.add_edge("day_planner", "conversation_agent")    # Present day plan to user

    # Compile 
    return workflow.compile()
