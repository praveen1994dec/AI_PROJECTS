"""
main.py
CLI entrypoint for running the agent loop.
"""

from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama
from langchain.agents import create_agent as create_react_agent

from config import SYSTEM_PROMPT, MODEL_NAME, TEMPERATURE
from tools import ALL_TOOLS


def main():
    # Initialize Ollama model
    llm = ChatOllama(model=MODEL_NAME, temperature=TEMPERATURE)
    
    # Create light react agent
    agent = create_react_agent(llm, ALL_TOOLS)

    print("\n🐳 Docker Troubleshooter Agent (RCA Enabled)")
    print("---------------------------------------------")
    print("Ask about your Docker containers. Type 'quit' to exit.\n")

    # Maintain conversation state
    messages_history = [SystemMessage(content=SYSTEM_PROMPT)]

    while True:
        try:
            user_input = input("> ").strip()
            if user_input.lower() in ("quit", "exit", "q"):
                print("Exiting Troubleshooter. Goodbye!")
                break
            if not user_input:
                continue

            print("\nAnalyzing Docker daemon...\n")
            
            messages_history.append(("user", user_input))

            # Run agent loop
            result = agent.invoke({"messages": messages_history})
            
            final_answer = result["messages"][-1].content
            print(final_answer)
            print()
            
            # Save assistant response to memory context
            messages_history.append(("assistant", final_answer))
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error during agent execution: {str(e)}\n")

if __name__ == "__main__":
    main()