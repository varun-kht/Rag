import os 
from langgraph.graph import StateGraph, END
from src.models import TicketState
from src.agents.triage import triage_node
from src.agents.retriever import retriever_node
from src.agents.writer import resolution_writer_node
from src.agents.compliance import compliance_node

def route_triage(state: TicketState):
    if state.get("missing_critical_info"):
        return "writer"
    return "retriever"

def route_compliance(state: TicketState):
    if state.get("compliance_passed"):
        return END
    
    # Check max iterations
    if state.get("iterations", 0) >= 3:
        print("Max iterations reached. Forcing escalation.")
        return END

    return "writer"

def build_graph():
    workflow = StateGraph(TicketState)
    
    workflow.add_node("triage", triage_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("writer", resolution_writer_node)
    workflow.add_node("compliance", compliance_node)
    
    workflow.set_entry_point("triage")
    
    workflow.add_conditional_edges("triage", route_triage)
    
    workflow.add_edge("retriever", "writer")
    workflow.add_edge("writer", "compliance")
    
    workflow.add_conditional_edges("compliance", route_compliance)
    
    return workflow.compile()
