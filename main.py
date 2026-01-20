import os
import json
from dotenv import load_dotenv
from graphs.workflow import create_travel_workflow

load_dotenv()

def main():
    print("--- Global Voyager Travel Planner ---")
    app = create_travel_workflow()
    
    # Load packages
    package_file = os.path.join("dataset", "Packages.json")
    with open(package_file, 'r') as f:
        packages = json.load(f)
        
    state = {
        "messages": [],
        "current_state": "greeting",
        "packages": packages,
        "use_alternative_plan": False
    }
    
    print("System Ready. Type 'exit' to quit.")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        from langchain_core.messages import HumanMessage
        state["messages"] = [HumanMessage(content=user_input)]
        
        try:
            state = app.invoke(state)
            if state["messages"]:
                print(f"\nAssistant: {state['messages'][-1].content}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
