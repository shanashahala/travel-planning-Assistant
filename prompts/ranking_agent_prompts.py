from graphs.state import AgentState

def ranking_agent_prompt(state:AgentState) -> str:
    prompt = f"""Rank these travel packages based on the research results.
    
    Research results:
    {state.get('research_results', 'No research results available')}
    
    Available Packages:
    {state.get('packages', [])}
    
    Provide your response in JSON format with the following structure:
    {{
        "ranked_packages": [
            {{
                "package_id": "string",
                "score": integer (0-100),
                "reasoning": "string"
            }}
        ],
        "top_recommendations": [
            {{
                "package_id": "string",
                "explanation": "string"
            }}
        ]
    }}
    
    Instruction:
    1. Rank from best to worst match.
    2. Provide a score for each package.
    3. Include reasoning for each ranking.
    4. Provide top recommendation with detailed explanation.
    """
    return prompt