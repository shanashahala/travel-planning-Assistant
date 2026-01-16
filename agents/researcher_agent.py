import json
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from graphs.state import AgentState
from prompts.researcher_prompt import researcher_prompt

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
# Agent definition
def researcher_agent(state: AgentState):
    """This agent researches the packages based on the user preferences"""
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", groq_api_key=groq_api_key)
    
    # Get the prompt string from our prompt function
    prompt_str = str(researcher_prompt(state))
    
    # Invoke the LLM
    response = llm.invoke([
        SystemMessage(content=prompt_str),
        HumanMessage(content="Filter the available packages based on the prioritized criteria and return ONLY the JSON list.")
    ])
    
    content = response.content.strip()
    
    # Robust JSON extraction from content
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
        
    try:
        packages = json.loads(content)
        # Ensure it's a list
        if not isinstance(packages, list):
            packages = [packages] if isinstance(packages, dict) else []
    except Exception as e:
        print(f"Error parsing researcher JSON: {e}")
        # Fallback to current packages
        packages = state.get('package', [])

    return {"research_results": packages}
