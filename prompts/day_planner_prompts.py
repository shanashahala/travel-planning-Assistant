from graphs.state import AgentState

def day_planner_prompt(state: AgentState) -> str:
    selected_package = state.get('selected_package', {})
    use_alternative = state.get('use_alternative_plan', False)
    
    plan_type = "ALTERNATIVE" if use_alternative else "PRIMARY"
    
    prompt = f"""You are a professional travel itinerary planner. 
    Based on the selected package, create a beautiful and detailed day-by-day itinerary.

    Selected Package:
    {selected_package}

    Planning Mode: {plan_type}
    
    Instructions:
    1. If Planning Mode is PRIMARY: Use only the 'primary_plan' from each day in the 'day_plans'.
    2. If Planning Mode is ALTERNATIVE: Use the 'alternative_plans' from each day in the 'day_plans'. 
       If multiple alternatives exist, pick the most interesting one that hasn't been suggested in previous messages.
       If alternative plans are exhausted for any day, notify the user.
    3. Return your response in JSON format with the following structure:
    {{
        "itinerary": [
            {{
                "day": integer,
                "plan": "string",
                "activities_detail": "string"
            }}
        ],
        "alternatives_available": boolean,
        "message": "string (A friendly summary for the user)"
    }}

    Rules:
    - Focus strictly on the {plan_type} plans provided in the package.
    - Make the activities sound exciting and professional.
    - 'alternatives_available' should be true if there are more options in 'alternative_plans' that haven't been used.
    """
    return prompt