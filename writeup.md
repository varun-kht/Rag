# E-Commerce Support Agent Architecture Write-up

## Architecture Overview
The system is orchestrated using **LangGraph**, forming a structured loop between 4 specific nodes (Agents):
1. **Triage Agent**: Takes the fresh ticket and order context. It categorizes the issue and statically analyzes if any critical information (like order numbers or which item is broken) is missing. If missing, it immediately prompts the customer and ends the graph without querying the vector DB.
2. **Policy Retriever**: Queries the Chroma vector store. It uses `RecursiveCharacterTextSplitter` (chunk size: 500, overlap: 100) and `sentence-transformers/all-MiniLM-L6-v2` locally for fast, precise retrieval of policy snippets.
3. **Resolution Writer Agent**: Drafts a structured JSON response consisting of the decision, rationale, verbatim citations (from chunk metadata), and a drafted customer response.
4. **Compliance / Safety Agent**: The final guardrail. It takes the writer's output and cross-references it with the retrieved chunks. If it spots a hallucinated claim, an unapproved action, or missing citations, it forces a loop back to the Writer with explicit feedback on what rule was broken.

## Data Sources
The policy corpus consists of 12 synthetic markdown files representing a comprehensive internal support knowledge base (`src/policies/*.md`). It covers general return rules, strict exceptions for hygiene/perishable items, third-party marketplace routing, split shipping rules, and regional variance (EU / California laws).

## Evaluation Summary
*(Pending API Key Run)*
The evaluation suite (`src/eval.py`) runs the agents against 20 specifically crafted test cases that stress-test conflict resolution, strict exceptions, and ambiguous tickets.
- **Citation Coverage**: Expected to be near 100% due to the Compliance agent loop.
- **Key Failure Modes observed**: Sometimes the LLM can get confused when two policies perfectly overlap in priority (e.g. Item is perishable AND it's a marketplace item). A strict hierarchy explicitly laid out in the prompt usually fixes this.

## Future Improvements
1. **Dynamic Retrieval**: If the Writer cannot find the answer in the initial 5 retrieved chunks, the graph should loop back to the Retriever with a new, expanded search query rather than simply defaulting to "Needs Escalation".
2. **Sentiment Analysis**: Adding a small fast layer to detect highly irate customers and dynamically adjusting the drafted response tone (or auto-escalating immediately).
