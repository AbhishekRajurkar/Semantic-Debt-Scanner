from langgraph.graph import StateGraph, END
from src.state import GraphState
from src.nodes import pop_file_node, semantic_router_node, local_critique_node, gemini_strategy_node, reflection_node

def route_after_pop(state: GraphState):
    """Conditional Edge: If queue is empty, break the loop and send to Gemini."""
    if state["current_file"] is None:
        return "gemini_strategy_node"
    return "semantic_router_node"

def route_from_router(state: GraphState):
    """Decide if we should analyze the file or skip it."""
    print(f"DEBUG: Router Decision in State: {state.get('router_decision')}")

    decision = state.get("router_decision", "skip") # Default to skip if missing
    if decision == "analyze":
        return "analyze" # This string must match the key in the mapping below
    return "skip"


def build_graph():
    builder = StateGraph(GraphState)
    
    builder.add_node("pop_file_node", pop_file_node)
    builder.add_node("semantic_router_node", semantic_router_node)
    builder.add_node("local_critique_node", local_critique_node)
    builder.add_node("reflection_node", reflection_node)
    builder.add_node("gemini_strategy_node", gemini_strategy_node)
    
    builder.set_entry_point("pop_file_node")
    
    # Loop Logic
    builder.add_conditional_edges("pop_file_node", route_after_pop)
    # 3. Add the conditional edge FROM the Router
    builder.add_conditional_edges(
        "semantic_router_node", 
        route_from_router,
        {
            "analyze": "local_critique_node",
            "skip": "pop_file_node"
        }
    )
    builder.add_edge("local_critique_node", "reflection_node")
    builder.add_edge("reflection_node", "pop_file_node")
    
    # End Logic
    builder.add_edge("gemini_strategy_node", END)
    
    return builder.compile()
