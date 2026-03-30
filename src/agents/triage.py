import os
from langchain_core.prompts import ChatPromptTemplate
from src.models import TicketState, TriageOutput

def get_llm():
    # Helper to load Groq LLM
    from langchain_groq import ChatGroq
    from dotenv import load_dotenv
    load_dotenv()
    # We use a fast, reasoning-capable model for these components.
    return ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

def triage_node(state: TicketState) -> TicketState:
    print("--- TRIAGE AGENT ---")
    llm = get_llm()
    structured_llm = llm.with_structured_output(TriageOutput)
    
    system_prompt = """You are the Triage Agent for an e-commerce customer support team. 
    Analyze the incoming support ticket and the provided order context.
    
    Your goal is to:
    1. Classify the issue type.
    2. Determine if any CRITICAL information is missing required to resolve the issue (e.g., they want a refund but didn't say for which item in a multi-item order).
    3. Generate up to 3 clarifying questions IF AND ONLY IF critical info is missing or ambiguous. 
       Do not ask questions if the policy can be applied to simply deny or approve the request based on current information.
       
    Order Context:
    {order_context}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Ticket details:\n{ticket_text}")
    ])
    
    chain = prompt | structured_llm
    
    res: TriageOutput = chain.invoke({
        "order_context": str(state["order_context"]),
        "ticket_text": state["ticket_text"]
    })
    
    return {
        "classification": res.classification,
        "missing_critical_info": res.missing_critical_info,
        "clarifying_questions": res.clarifying_questions
    }
