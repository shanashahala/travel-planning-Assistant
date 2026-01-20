from graphs.state import AgentState
import json

def ranking_agent_prompt(state: AgentState) -> str:
    research_results = state.get('research_results', [])
    preferences = {
        "package_type": state.get('package_type'),
        "destination": state.get('destination'),
        "budget": state.get('budget'),
        "duration_days": state.get('duration_days'),
        "traveler_type": state.get('traveler_type'),
        "activities": state.get('activities', [])
    }
    
    return f"""
    You are a Professional Travel Package Analyst. Your goal is to rank the candidate packages based on how well they match the user's specific preferences.

    USER PREFERENCES:
    {json.dumps(preferences, indent=2)}

    CANDIDATE PACKAGES (from Research):
    {json.dumps(research_results, indent=2)}

    RANKING CRITERIA:
    1. **Primary Match**: Total alignment with "package_type" and "destination".
    2. **Secondary Match**: Matches the "duration_days" and stays within the "budget" (consider traveler_type for price).
    3. **Tertiary Match**: Includes requested "activities" in the itinerary.

    INSTRUCTIONS:
    - Return the FULL package objects in a list, sorted from best match to least.
    - Do not add any new packages.
    - For the budget check, use the price corresponding to the user's "traveler_type" (solo, couple, or family_4).

    OUTPUT FORMAT:
    Return ONLY a JSON object:
    {{
        "ranked_packages": [
            {{ ... full package object 1 ... }},
            {{ ... full package object 2 ... }}
        ]
    }}
    """.strip()