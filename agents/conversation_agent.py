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
    Primary Conversational Travel Agent that guides the user.
    It uses the conversation_prompt to generate a response based on current state.
    """
    # 1. Initialize the LLM
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", groq_api_key=groq_api_key)
    
    # 2. Get the system prompt based on current state
    system_prompt = conversation_prompt(state)
    
    # 3. Prepare messages for the LLM
    # The state['messages'] already contains the history handled by add_messages
    messages = [SystemMessage(content=system_prompt)] + state.get('messages', [])
    
    # 4. Invoke LLM
    response = llm.invoke(messages)
    
    # 5. Return the response to be added to messages
    return {"messages": [response]}
