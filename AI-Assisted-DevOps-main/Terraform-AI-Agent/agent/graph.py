from langgraph.graph import StateGraph, START, END
from agent.state import AgentState
from agent.nodes import call_model, tool_node

def should_continue(state: AgentState) -> str:
    """
    Determines the next step in the graph.
    If the LLM decided to call a tool (e.g., validate_code), route to 'tools'.
    If the LLM returned a final text response, route to END.
    """
    last_message = state["messages"][-1]
    
    if last_message.tool_calls:
        return "tools"
    return END

workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", END: END}
)

workflow.add_edge("tools", "agent")

terraform_agent = workflow.compile()