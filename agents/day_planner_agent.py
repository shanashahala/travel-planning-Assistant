import os
import json
import logging
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage
from prompts.day_planner_prompts import day_planner_prompt
from graphs.state import AgentState
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("day_planner_agent")

def day_planner_agent(state: AgentState) -> Dict[str, Any]:
    """
    Agent responsible for preparing the day-by-day itinerary.
    """
    logger.info("DayPlannerAgent invoked")
    
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

        content = response.content.strip()
        
        # Robust JSON extraction
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        try:
            parsed_data = json.loads(content)
            
            day_plan = parsed_data.get("itinerary", [])
            msg = parsed_data.get("message", "Your itinerary is ready!")
            
            logger.info(f"Day plan generated with {len(day_plan)} days.")
            
            return {
                "day_plan": day_plan,
                "current_state": "plan_review",
                "messages": [AIMessage(content=msg)]
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Day Planner LLM response: {e}")
            return {
                "current_state": "plan_review",
                "messages": [AIMessage(content="I encountered an issue generating your itinerary. Let me try again.")]
            }

    except Exception as e:
        logger.error(f"Day Planner Error: {e}")
        return {
            "messages": [AIMessage(content=f"Error generating itinerary: {str(e)}")]
        }
