import json
import os
from src.graph import build_graph
from src.models import TicketState

test_cases = [
    # 8 Standard
    {"type": "standard", "text": "I want to return my unworn t-shirt. It doesn't fit.", "context": {"item_category": "apparel", "order_status": "delivered", "fulfillment_type": "first-party", "shipping_region": "USA"}},
    {"type": "standard", "text": "Can I cancel my order? I just placed it 10 minutes ago.", "context": {"item_category": "electronics", "order_status": "placed", "fulfillment_type": "first-party", "shipping_region": "USA"}},
    {"type": "standard", "text": "My package hasn't moved in tracking for 10 days. I think it's lost.", "context": {"item_category": "home", "order_status": "shipped", "fulfillment_type": "first-party", "shipping_region": "USA"}},
    {"type": "standard", "text": "I ordered a green plate but got a blue one. I want a replacement.", "context": {"item_category": "kitchen", "order_status": "delivered", "fulfillment_type": "first-party", "shipping_region": "USA"}},
    {"type": "standard", "text": "How long will my standard shipping take?", "context": {"item_category": "books", "order_status": "shipped", "fulfillment_type": "first-party", "shipping_region": "USA"}},
    {"type": "standard", "text": "My coupon code START10 wasn't applied. Can you refund me the 10%?", "context": {"item_category": "beauty", "order_status": "delivered", "fulfillment_type": "first-party", "shipping_region": "USA"}},
    {"type": "standard", "text": "Part of my order is missing! Only the shoes arrived, not the socks.", "context": {"item_category": "apparel", "order_status": "delivered", "fulfillment_type": "first-party", "shipping_region": "USA"}},
    {"type": "standard", "text": "I got an overnight shipping order but it was 2 days late. I want a shipping refund.", "context": {"item_category": "electronics", "order_status": "delivered", "fulfillment_type": "first-party", "shipping_region": "USA"}},

    # 6 Exceptions
    {"type": "exception", "text": "I took a bite of this cheese and didn't like it. Refund me.", "context": {"item_category": "perishable", "order_status": "delivered", "fulfillment_type": "first-party", "shipping_region": "USA"}},
    {"type": "exception", "text": "I tried on these undergarments and they are too tight. I want to return them.", "context": {"item_category": "hygiene", "order_status": "delivered", "fulfillment_type": "first-party", "shipping_region": "USA"}},
    {"type": "exception", "text": "Returning this clearance jacket.", "context": {"item_category": "apparel", "order_status": "delivered", "fulfillment_type": "first-party", "shipping_region": "USA", "sale_type": "Final Sale"}},
    {"type": "exception", "text": "I used the software code but my computer is too slow to run it. Refund please.", "context": {"item_category": "digital", "order_status": "delivered", "fulfillment_type": "first-party", "shipping_region": "USA"}},
    {"type": "exception", "text": "My bananas arrived completely rotten and black.", "context": {"item_category": "perishable", "order_status": "delivered", "fulfillment_type": "first-party", "shipping_region": "USA"}},
    {"type": "exception", "text": "The custom engraved ring is too small. Please exchange.", "context": {"item_category": "personalized", "order_status": "delivered", "fulfillment_type": "first-party", "shipping_region": "USA", "sale_type": "Final Sale"}},

    # 3 Conflict
    {"type": "conflict", "text": "I want to return this. It's day 13.", "context": {"item_category": "electronics", "order_status": "delivered", "fulfillment_type": "first-party", "shipping_region": "EU"}},
    {"type": "conflict", "text": "The 3rd party seller gave me a broken lamp and hasn't responded in 3 days. I want my money back.", "context": {"item_category": "home", "order_status": "delivered", "fulfillment_type": "marketplace", "shipping_region": "USA"}},
    {"type": "conflict", "text": "I live in California. Can I cash out my $5 gift card?", "context": {"item_category": "gift_card", "order_status": "delivered", "fulfillment_type": "first-party", "shipping_region": "California"}},

    # 3 Missing / Not-in-policy
    {"type": "missing", "text": "My thing is broken. Replace it.", "context": {"item_category": "mixed", "order_status": "delivered", "fulfillment_type": "first-party", "shipping_region": "USA"}}, # Missing critical info (which thing?)
    {"type": "missing", "text": "I want to cancel.", "context": {"item_category": "mixed", "order_status": "processing", "fulfillment_type": "first-party", "shipping_region": "USA"}}, # Missing info (need order number/confirmation to cancel)
    {"type": "not_in_policy", "text": "Your CEO sucks. Give me 1000 dollars free or I sue.", "context": {"item_category": "none", "order_status": "none", "fulfillment_type": "first-party", "shipping_region": "USA"}}
]

def run_evaluation():
    from dotenv import load_dotenv
    if not load_dotenv() or not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not found in .env. Plase provide one to run eval.")
        return

    print("Building graph...")
    app = build_graph()
    results = []

    print(f"Running evaluation on {len(test_cases)} test cases...")
    for i, case in enumerate(test_cases):
        print(f"\\n--- Running Case {i+1}/{len(test_cases)} ({case['type']}) ---")
        state = TicketState(
            ticket_id=f"TKT-{i}",
            ticket_text=case["text"],
            order_context=case["context"],
            iterations=0,
            compliance_passed=False
        )
        
        import time
        time.sleep(4) # Respect Groq free-tier RPM/TPM limits
        try:
            final_state = app.invoke(state)
            results.append({
                "case": case,
                "output": {
                    "classification": final_state.get("classification"),
                    "decision": final_state.get("decision"),
                    "rationale": final_state.get("rationale"),
                    "citations": final_state.get("citations", []),
                    "draft_response": final_state.get("draft_response"),
                    "missing_info": final_state.get("missing_critical_info", False),
                    "questions": final_state.get("clarifying_questions", [])
                }
            })
        except Exception as e:
            print(f"Error on case {i}: {e}")
            results.append({"case": case, "error": str(e)})

    # Calculate metrics
    total = len(results)
    citation_count = sum(1 for r in results if r.get("output") and len(r["output"].get("citations", [])) > 0)
    
    # Missing info checks
    missing_cases = [r for r in results if r["case"]["type"] == "missing"]
    asked_questions_count = sum(1 for r in missing_cases if r.get("output") and r["output"]["missing_info"])
    
    # Conflict checks
    conflict_cases = [r for r in results if r["case"]["type"] == "conflict"]
    escalated_or_resolved = sum(1 for r in conflict_cases if r.get("output") and r["output"]["decision"] in ["needs_escalation", "approve", "partial"])

    print("\\n=== EVALUATION REPORT ===")
    print(f"Total Tickets Processed: {total}")
    print(f"Citation Coverage Rate: {citation_count}/{total} ({(citation_count/total)*100:.1f}%)")
    print(f"Handled Missing Info (Questions Asked): {asked_questions_count}/{len(missing_cases)}")
    
    # Save results to a file
    with open("eval_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Full results saved to eval_results.json")
    
if __name__ == "__main__":
    run_evaluation()
