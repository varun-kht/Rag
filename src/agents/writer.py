from langchain_core.prompts import ChatPromptTemplate
from src.agents.triage import get_llm
from src.models import TicketState, WriterOutput

def resolution_writer_node(state: TicketState) -> TicketState:
    print("--- RESOLUTION WRITER AGENT ---")
    
    # If triage said we need info, the writer just outputs the questions.
    if state.get("missing_critical_info") and state.get("clarifying_questions"):
        questions_text = "\n".join([f"- {q}" for q in state["clarifying_questions"]])
        draft = f"Hello,\n\nThank you for contacting ABC support. To better assist you, could you please provide a bit more information?\n{questions_text}\n\nBest regards,\nABC Support"
        
        return {
            "decision": "needs_more_info",
            "rationale": "Ticket is missing critical context required to make a decision.",
            "citations": [],
            "draft_response": draft,
            "next_steps": "Wait for customer reply."
        }

    llm = get_llm()
    structured_llm = llm.with_structured_output(WriterOutput)
    
    # Format retrieved chunks
    context_str = ""
    for i, c in enumerate(state.get("retrieved_chunks", [])):
        title = c["metadata"].get("title", "Unknown Doc")
        chunk_id = c["metadata"].get("chunk_id", f"chunk_{i}")
        context_str += f"[{title} - {chunk_id}]\n{c['content']}\n\n"
        
    system_prompt = """You are the Resolution Writer Agent for an e-commerce support team.
    Draft the final customer response based strictly on the provided policy context.
    
    RULES:
    1. NEVER invent or hallucinate policies. Only use the provided Policy Excerpts.
    2. If the request is 'out of policy', politely deny it based strictly on the excerpt.
    3. If policies conflict (e.g. state law vs general policy), follow the escalation path or choose the most legally compliant one if explicitly stated.
    4. Reference the provided citations to back up your rationale.
    5. The draft response should be customer-ready, professional, and empathetic.
    """
    
    human_prompt = """Ticket:
    {ticket_text}
    
    Order Context:
    {order_context}
    
    Policy Excerpts:
    {context_str}
    
    Provide your decision, rationale, exact citations, and the draft response.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    chain = prompt | structured_llm
    res: WriterOutput = chain.invoke({
        "ticket_text": state["ticket_text"],
        "order_context": str(state["order_context"]),
        "context_str": context_str
    })
    
    return {
        "decision": res.decision,
        "rationale": res.rationale,
        "citations": res.citations,
        "draft_response": res.draft_response,
        "next_steps": res.next_steps
    }
