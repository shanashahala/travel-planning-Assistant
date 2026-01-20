from typing import TypedDict, Annotated, Literal, List, Dict, Any, Optional
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    Shared state across all agents in the travel planner workflow.
    This state is passed between agents and updated as the conversation progresses.
    """
    # Conversation agent
    messages: Annotated[List[Any],add_messages] #full conversation history with system prompt
    current_state: str  # greeting, package_type_selection, destination_selection, etc.

    # info collector agent
    package_type: Optional[str]  # beach, hills, heritage, honeymoon, adventure, pilgrimage
    destination: Optional[str]  # Goa, Manali, etc.
    available_destinations: Optional[List[str]]  # Destinations available for selected package_type
    budget: Optional[float]  # User's budget constraint
    duration_days: Optional[int]  # Preferred trip duration
    traveler_type: Optional[str]  # solo, couple, family_4
    activities:Optional[List[str]] #user preffered activities

    research_results: Optional[List[Dict[str, Any]]]  # Packages found by research agent
    ranked_packages:Optional[List[Dict[str,Any]]] #list of Ranked packages
    selected_package:Optional[Dict[str,Any]] # user selected package
    day_plan:Optional[List[Dict[str,Any]]] # day plan for selected package
    use_alternative_plan: bool  # Whether to use alternative plans
    package_confirmed: Optional[bool] # Whether the user confirmed the selected package
    last_package_confirmed: Optional[bool] # Track the last decision to handle the ranking loop
   
    #packages
    packages:List[Dict] #list of packages
