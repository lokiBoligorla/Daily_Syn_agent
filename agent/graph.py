from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes.task_processor import process_tasks_node
from agent.nodes.excel_updater import excel_updater_node
from agent.nodes.email_generator import email_generator_node
from agent.nodes.email_sender import email_sender_node

def route_after_generation(state: AgentState):
    """
    Conditional routing: If preview_mode is enabled, stop. Otherwise, send email.
    """
    if state.get("preview_mode", False):
        return "stop"
    return "send_email"

def create_agent_graph():
    """
    Compiles and returns the LangGraph workflow.
    """
    workflow = StateGraph(AgentState)
    
    # 1. Register nodes
    workflow.add_node("task_processor", process_tasks_node)
    workflow.add_node("excel_updater", excel_updater_node)
    workflow.add_node("email_generator", email_generator_node)
    workflow.add_node("email_sender", email_sender_node)
    
    # 2. Define standard flow
    workflow.set_entry_point("task_processor")
    workflow.add_edge("task_processor", "excel_updater")
    workflow.add_edge("excel_updater", "email_generator")
    
    # 3. Add conditional edge after generation
    workflow.add_conditional_edges(
        "email_generator",
        route_after_generation,
        {
            "stop": END,
            "send_email": "email_sender"
        }
    )
    
    # 4. Standard edge from sender to END
    workflow.add_edge("email_sender", END)
    
    # Compile
    return workflow.compile()
