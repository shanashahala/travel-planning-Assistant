import os
import json
import logging
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage
from prompts.day_planner_prompts import day_planner_prompt
from graphs.state import AgentState
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("day_planner_agent")

def day_planner_agent(state: AgentState) -> AgentState:
    """
    Agent responsible for preparing the day-by-day itinerary.
    """
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found")

        llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0.2,
            groq_api_key=api_key
        )

        prompt_text = day_planner_prompt(state)
        response = llm.invoke(prompt_text)
        
        logger.info(f"Day Planner Raw Response: {response.content}")

        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            parsed_data = json.loads(content)
            
            # Store the plan in the state
            state["day_plan"] = parsed_data.get("itinerary", [])
            
            # Check if alternatives are exhausted
            if state.get("use_alternative_plan") and not parsed_data.get("alternatives_available"):
                msg = "I've suggested all possible alternatives for this package."
            else:
                msg = parsed_data.get("message", "Your itinerary is ready!")

            state["messages"].append(AIMessage(content=msg))

        except json.JSONDecodeError:
            logger.error("Failed to parse Day Planner LLM response")
            state["messages"].append(AIMessage(content="Error generating the itinerary."))

        return state

    except Exception as e:
        logger.error(f"Day Planner Error: {e}")
        return state
