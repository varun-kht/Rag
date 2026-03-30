from langchain_core.prompts import ChatPromptTemplate
from src.agents.triage import get_llm
from src.models import TicketState, ComplianceOutput

def compliance_node(state: TicketState) -> TicketState:
    print("--- COMPLIANCE / SAFETY AGENT ---")
    
    # If it was just asking for missing info, skip compliance
    if state.get("decision") == "needs_more_info":
        return {"compliance_passed": True, "iterations": state.get("iterations", 0)}

    llm = get_llm()
    structured_llm = llm.with_structured_output(ComplianceOutput)
    
    context_str = ""
    for i, c in enumerate(state.get("retrieved_chunks", [])):
        title = c["metadata"].get("title", "Unknown Doc")
        chunk_id = c["metadata"].get("chunk_id", f"chunk_{i}")
        context_str += f"[{title} - {chunk_id}]\n{c['content']}\n\n"
        
    system_prompt = """You are the Strict Compliance and Safety Agent.
    Your job is to review the Resolution Writer's draft response and rationale.
    
    Check for the following FATAL ERRORS:
    1. Unsupported Claims (Hallucination): Does the draft promise something that is NOT explicitly allowed in the provided Policy Excerpts? 
    2. Missing Citations: Are there decisions made without proper citations?
    3. Policy Violations: Did the writer approve something that the policy explicitly says to deny?
    4. Safety issues: Is the response combative or unprofessional?
    
    If ANY of these errors are present, set passed=False and provide explicit feedback on what rule was broken so the Writer can fix it.
    If the response is perfectly aligned with the retrieved policy excerpts and is professional, set passed=True and feedback empty.
    """
    
    human_prompt = """Policy Excerpts:
    {context_str}
    
    Ticket: {ticket_text}
    
    Writer's Decision: {decision}
    Writer's Rationale: {rationale}
    Writer's Citations: {citations}
    Writer's Draft Response: {draft_response}
    
    Analyze the Writer's output based strictly on the Policy Excerpts.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    chain = prompt | structured_llm
    res: ComplianceOutput = chain.invoke({
        "context_str": context_str,
        "ticket_text": state["ticket_text"],
        "decision": state["decision"],
        "rationale": state["rationale"],
        "citations": str(state["citations"]),
        "draft_response": state["draft_response"]
    })
    
    current_iterations = state.get("iterations", 0) + 1
    
    if not res.passed:
        print(f"Compliance failed! Feedback: {res.feedback}")
        
    return {
        "compliance_passed": res.passed,
        "iterations": current_iterations,
        # If it failed compliance, we append the feedback so the writer sees what to fix
        "rationale": state["rationale"] + f"\n\n[COMPLIANCE FEEDBACK]: {res.feedback}" if not res.passed else state["rationale"]
    }
