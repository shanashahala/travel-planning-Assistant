import streamlit as st
import os
import json
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from graphs.workflow import create_travel_workflow

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(page_title="Global Voyager - AI Travel Planner", page_icon="✈️", layout="centered")

# Custom CSS for premium look
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stChatMessage {
        border-radius: 15px;
        margin-bottom: 10px;
    }
    .stChatInput {
        border-top: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

# App header
st.title("✈️ Global Voyager")
st.subheader("Your AI-powered personalized travel architect")

# Initialize workflow
@st.cache_resource
def get_workflow():
    return create_travel_workflow()

workflow_app = get_workflow()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent_state" not in st.session_state:
    # Load initial packages
    base_dir = os.path.dirname(os.path.abspath(__file__))
    package_file = os.path.join(base_dir, "dataset", "Packages.json")
    try:
        with open(package_file, 'r') as f:
            packages = json.load(f)
    except Exception as e:
        st.error(f"Error loading packages: {e}")
        packages = []

    st.session_state.agent_state = {
        "messages": [],
        "current_state": "greeting",
        "packages": packages,
        "package_type": None,
        "destination": None,
        "budget": None,
        "duration_days": None,
        "traveler_type": None,
        "activities": [],
        "available_destinations": [],
        "research_results": [],
        "ranked_packages": [],
        "selected_package": {},
        "day_plan": [],
        "use_alternative_plan": False,
        "alternatives_available": False
    }
    
    # Trigger initial greeting
    with st.spinner("Initializing Travel Assistant..."):
        try:
            initial_state = st.session_state.agent_state.copy()
            initial_state["messages"] = [HumanMessage(content="hello")]
            result = workflow_app.invoke(initial_state)
            st.session_state.agent_state = result
            if result["messages"]:
                last_msg = result["messages"][-1]
                if isinstance(last_msg, AIMessage):
                    st.session_state.messages.append({"role": "assistant", "content": last_msg.content})
        except Exception as e:
            st.error(f"Error during initialization: {e}")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
if prompt := st.chat_input("Tell me about your dream vacation..."):
    # Add user message to UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process with LangGraph
    with st.spinner("Planning your journey..."):
        # Prepare state for agent
        current_state = st.session_state.agent_state
        current_state["messages"] = [HumanMessage(content=prompt)]
        
        # Run workflow
        # Note: In a conversation loop, we usually run the graph until it reaches an update point
        # For simplicity, we run the graph once for the turn
        config = {"configurable": {"thread_id": "streamlit_chat"}}
        
        try:
            # We use invoke to get the final state after one turn
            result = workflow_app.invoke(current_state, config=config)
            
            # Update session state with new agent state
            st.session_state.agent_state = result
            
            # Extract AI message
            if result["messages"]:
                last_msg = result["messages"][-1]
                if isinstance(last_msg, AIMessage):
                    ai_response = last_msg.content
                    
                    # Add to UI
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    with st.chat_message("assistant"):
                        st.markdown(ai_response)
                        
                        # Show debug info in expander if needed
                        with st.expander("System Insights"):
                            st.write(f"**Current State:** {result.get('current_state')}")
                            if result.get('selected_package'):
                                st.write(f"**Selected Package:** {result['selected_package'].get('destination')}")
                            if result.get('day_plan'):
                                st.write("**Itinerary Generated**")
        
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.write(e)

# Sidebar for Preferences
with st.sidebar:
    st.header("📋 Your Preferences")
    state = st.session_state.agent_state
    
    st.info(f"**Stage:** {state.get('current_state', 'None').replace('_', ' ').title()}")
    
    if state.get('package_type'):
        st.write(f"🏙️ **Type:** {state['package_type']}")
    if state.get('destination'):
        st.write(f"📍 **Dest:** {state['destination']}")
    if state.get('budget'):
        st.write(f"💰 **Budget:** {state['budget']}")
    if state.get('duration_days'):
        st.write(f"⏱️ **Days:** {state['duration_days']}")
    if state.get('traveler_type'):
        st.write(f"👥 **Travelers:** {state['traveler_type']}")
    
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        del st.session_state.agent_state
        st.rerun()
