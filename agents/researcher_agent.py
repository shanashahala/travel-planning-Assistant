import json
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from graphs.state import AgentState
from prompts.researcher_prompt import researcher_prompt
from utils.matcher import get_most_similar_packages

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")


def researcher_agent(state: AgentState):
    """This agent researches the packages based on the user preferences or finds similar ones"""
    
    # 1. Load all packages if not already in state
    all_packages = state.get('packages', [])
    if not all_packages:
        # Load from local dataset/Packages.json
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        package_file = os.path.join(base_dir, "dataset", "Packages.json")
        try:
            with open(package_file, 'r') as f:
                all_packages = json.load(f)
        except Exception as e:
            print(f"Error loading packages from {package_file}: {e}")
            all_packages = []

    # 2. Find most similar packages using our matching function
    # This handles the "match user preferences not exactly found" requirement
    similar_packages = get_most_similar_packages(state, all_packages, limit=10)
    
    # Create a temporary state for the prompt with filtered packages
    temp_state = state.copy()
    temp_state['packages'] = similar_packages

    # 3. Use LLM to refine the selection and format the output
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", groq_api_key=groq_api_key)
    
    # Get the prompt string from our prompt function
    prompt_str = str(researcher_prompt(temp_state))
    
    # Invoke the LLM
    response = llm.invoke([
        SystemMessage(content=prompt_str),
        HumanMessage(content="Suggest the best packages from the list, prioritizing similarity where an exact match isn't found.")
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
        # Fallback to the top 3 similar packages found by the matcher
        packages = similar_packages[:3]

    return {"research_results": packages}
