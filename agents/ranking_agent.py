import os
import json
import logging
# from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from prompts.ranking_agent_prompts import ranking_agent_prompt
from graphs.state import AgentState
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ranking_agent")

def ranking_agent(state: AgentState) -> AgentState:
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found")

        llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0.2,
            groq_api_key=api_key
        )

        prompt_text = ranking_agent_prompt(state)
        response = llm.invoke(prompt_text)
        
        logger.info(f"Raw Response: {response.content}")

        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            parsed_data = json.loads(content)
            ranked_packages_data = parsed_data.get("ranked_packages", [])
            
            state["ranked_packages"] = ranked_packages_data
            
            if ranked_packages_data:
                top_pkg_id = ranked_packages_data[0].get("package_id")
                full_packages = state.get("packages", [])
                selected = next((p for p in full_packages if p.get("package_id") == top_pkg_id), {})
                state["selected_package"] = selected
            
            state["messages"].append(AIMessage(content=f"Ranked packages. Top match: {state.get('selected_package', {}).get('destination', 'None')}"))

        except json.JSONDecodeError:
            logger.error("Failed to parse LLM response")
            state["ranked_packages"] = []
            state["messages"].append(AIMessage(content="Error ranking packages."))

        return state

    except Exception as e:
        logger.error(f"Error: {e}")
        return state
