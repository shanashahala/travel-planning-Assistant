import os
import json
import logging
from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_groq import ChatGroq
from prompts.ranking_agent_prompts import ranking_agent_prompt
from graphs.state import AgentState
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ranking_agent")

def ranking_agent(state: AgentState) -> Dict[str, Any]:
    """
    Ranks packages based on research results.
    Handles the iteration loop: if the user rejects a package, it pops the next one.
    """
    logger.info("RankingAgent invoked")
    
    ranked_packages = state.get("ranked_packages", [])
    package_confirmed = state.get("package_confirmed")
    selected_package = state.get("selected_package")
    research_results = state.get("research_results", [])

    # Iteration Logic: If user rejected the previous recommendation
    if package_confirmed is False and selected_package:
        if ranked_packages:
            next_pkg = ranked_packages.pop(0)
            logger.info(f"User rejected previous package. Popping next: {next_pkg.get('destination')}")
            return {
                "selected_package": next_pkg,
                "ranked_packages": ranked_packages,
                "package_confirmed": None,
                "current_state": "show_packages"
            }
        else:
            logger.info("No more ranked packages available.")
            return {
                "selected_package": None,
                "ranked_packages": [],
                "current_state": "all_packages_shown", # Custom state to handle exhaustion
                "package_confirmed": None
            }

    # If we already have a selection and no rejection/confirmation, just stay put
    if selected_package and package_confirmed is None:
        logger.info("Selection already exists and waiting for confirmation.")
        return {}

    # Perform initial ranking if research_results are present and we haven't ranked them yet
    if not research_results:
        logger.warning("No research results to rank.")
        return {"ranked_packages": []}

    try:
        api_key = os.getenv("GROQ_API_KEY")
        llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0.1,
            groq_api_key=api_key
        )

        prompt_text = ranking_agent_prompt(state)
        response = llm.invoke(prompt_text)
        content = response.content.strip()

        # Robust JSON extraction
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        parsed_data = json.loads(content)
        all_ranked = parsed_data.get("ranked_packages", [])

        if not all_ranked:
            logger.warning("LLM returned no ranked packages.")
            return {"ranked_packages": []}

        # Pop the first one as selected
        final_list = list(all_ranked)
        top_selection = final_list.pop(0)
        
        logger.info(f"Initial ranking complete. Selected: {top_selection.get('destination')}. Remaining: {len(final_list)}")

        return {
            "selected_package": top_selection,
            "ranked_packages": final_list,
            "package_confirmed": None,
            "current_state": "show_packages"
        }

    except Exception as e:
        logger.error(f"Ranking error: {e}")
        # Fallback to research results if LLM fails
        if research_results:
            fallback_list = list(research_results)
            top = fallback_list.pop(0)
            return {"selected_package": top, "ranked_packages": fallback_list}
        return {"ranked_packages": []}
