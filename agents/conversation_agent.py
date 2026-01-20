import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from graphs.state import AgentState
from prompts.conversation_prompt import conversation_prompt

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

def conversation_agent(state: AgentState):
    """
    Primary Conversation Manager that parses stages and handles off-topics.
    """
    # 1. Initialize the LLM
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", groq_api_key=groq_api_key)
    
    # 2. Get the system prompt based on current state
    system_prompt = conversation_prompt(state)
    
    # 3. Prepare messages for the LLM
    messages = [SystemMessage(content=system_prompt)] + state.get('messages', [])
    
    # 4. Invoke LLM
    response = llm.invoke(messages)
    content = response.content.strip()
    
    # 5. Robust JSON parsing
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
        
    try:
        data = json.loads(content)
        new_state = data.get("current_state", state.get("current_state", "greeting"))
        ai_message = data.get("message", "I'm here to help with your travel plans!")
        package_confirmed = data.get("package_confirmed")
    except Exception as e:
        print(f"Error parsing conversation JSON: {e}")
        # Fallback
        new_state = state.get("current_state", "greeting")
        ai_message = content 
        package_confirmed = None
    
    # 6. Return updated state and message
    from langchain_core.messages import AIMessage
    return {
        "messages": [AIMessage(content=ai_message)],
        "current_state": new_state,
        "package_confirmed": package_confirmed
    }
