import json
from src.graph import build_graph
from src.models import TicketState

def main():
    from dotenv import load_dotenv
    import os
    if not load_dotenv() or not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not found in .env. Please provide one to run the interactive CLI.")
        return

    print("Building LangGraph...")
    app = build_graph()
    
    # Example interactive state
    ticket_text = input("Enter support ticket text: ")

    state = TicketState(
        ticket_id="TEST-1",
        ticket_text=ticket_text,
        order_context={
            "item_category": "electronics",
            "order_status": "delivered",
            "fulfillment_type": "first-party",
            "shipping_region": "USA"
        },
        iterations=0,
        compliance_passed=False
    )

    print("\n--- Running Graph ---")
    final_state = app.invoke(state)
    
    print("\n=== FINAL RESULT ===")
    print(f"Classification: {final_state.get('classification')}")
    print(f"Decision: {final_state.get('decision')}")
    print(f"Rationale: {final_state.get('rationale')}")
    print(f"Citations: {final_state.get('citations')}")
    print(f"Next Steps: {final_state.get('next_steps')}")
    
    if final_state.get('missing_critical_info'):
        print(f"Questions Asked: {final_state.get('clarifying_questions')}")
        
    print(f"\nDraft Response:\n{final_state.get('draft_response')}\n")

if __name__ == "__main__":
    main()
