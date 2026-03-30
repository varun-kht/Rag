# E-commerce Support Resolution Agent

A multi-agent RAG system built with LangGraph that processes customer support tickets and generates policy-grounded resolutions. Built as part of an assessment on hallucination-controlled, citation-backed AI pipelines.

---

## What It Does

Given a support ticket and structured order context, the system routes through four agents to produce a structured resolution — classification, decision, citations, a customer-ready response, and internal notes. Every policy claim must be backed by a retrieved chunk; the compliance agent blocks the response if citations are missing or a claim is unsupported.

Tickets it's designed to handle:
- Policy exceptions (final sale, hygiene items, perishables, opened items)
- Regional differences (country/state-level rules)
- Marketplace complexity (seller-fulfilled vs first-party)
- Ambiguous tickets with missing order info
- Out-of-policy demands (escalates or abstains — does not guess)

---

## Architecture

Four agents wired together via LangGraph:

| Agent | Responsibility |
|---|---|
| **Triage** | Classifies issue type, flags missing fields, generates clarifying questions |
| **Policy Retriever** | Queries ChromaDB, returns top-k chunks with doc title + chunk ID |
| **Resolution Writer** | Drafts response using only retrieved evidence — no unsupported claims |
| **Compliance / Safety** | Reviews draft for unsupported statements and missing citations — forces rewrite or escalates |

State flows through a `TicketState` object. The compliance agent is the last gate before any response is considered final.

---

## Stack

- **Orchestration:** LangGraph  
- **LLM:** Groq (`llama-3.3-70b-versatile`) via `langchain-groq`  
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (local, no API cost)  
- **Vector Store:** ChromaDB  
- **Structured Outputs:** Pydantic (`TriageOutput`, `TicketState`)  
- **Policy Corpus:** Synthetic e-commerce policy pack — 12 documents covering returns, cancellations, shipping, promotions, and disputes  

**Chunking:** 500 tokens, 50 token overlap. Small overlap is intentional — policy sections are self-contained, larger overlaps caused duplicate evidence in retrieval.  
**Retriever:** top-k = 4, no metadata filters.

---

## Setup

### 1. Clone and create a virtual environment
```bash
git clone https://github.com/varun-kht/Rag.git
cd Rag
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment

Copy `.env.example` to `.env` and add your Groq API key:
```
GROQ_API_KEY=your_api_key_here
```

Free-tier Groq keys work. Sign up at [console.groq.com](https://console.groq.com).

---

## Running the System

### Ingest policy documents

Embeds the corpus and builds the ChromaDB vector store locally. Run once:
```bash
python -m src.ingest
```

### Run the evaluation suite

20 test cases across 4 categories. Outputs metrics + full traces to `eval_results.json`:
```bash
python -m src.eval
```

### Interactive CLI

Test a single ticket end-to-end:
```bash
python -m src.main
```

---

## Input Format
```json
{
  "ticket": "My order arrived late and the cookies are melted. I want a full refund and to keep the item.",
  "order_context": {
    "order_date": "2024-06-01",
    "delivery_date": "2024-06-07",
    "item_category": "perishable",
    "fulfillment_type": "first-party",
    "shipping_region": "US-CA",
    "order_status": "delivered",
    "payment_method": "credit_card"
  }
}
```

---

## Output Format

Every resolution includes:

1. **Classification** — issue type  
2. **Clarifying Questions** — up to 3, if required fields are missing  
3. **Decision** — `approve` / `deny` / `partial` / `escalate`  
4. **Rationale** — policy-based explanation  
5. **Citations** — doc title + chunk ID for every claim  
6. **Customer Response Draft** — ready to send  
7. **Internal Notes** — recommended next steps for the support team  

---

## Evaluation

| Category | Count |
|---|---|
| Standard cases | 8 |
| Exception-heavy cases | 6 |
| Conflict cases | 3 |
| Not-in-policy cases | 3 |
| **Total** | **20** |

| Metric | Result |
|---|---|
| Citation coverage | run `python -m src.eval` |
| Unsupported claim rate | run `python -m src.eval` |
| Correct escalation rate | run `python -m src.eval` |

---

## Project Structure
```
.
├── src/
│   ├── agents/         # Triage, retriever, writer, compliance
│   ├── policies/       # Synthetic policy documents
│   ├── graph.py        # LangGraph state machine and routing
│   ├── models.py       # Pydantic output schemas
│   ├── ingest.py       # Document ingestion + embedding pipeline
│   ├── eval.py         # 20-case evaluation suite
│   └── main.py         # Interactive CLI
├── requirements.txt
├── writeup.md
└── .env.example
```

---

## Known Limitations

- Compliance agent occasionally over-escalates on ambiguous perishable cases where policy clauses overlap
- No streaming — full resolution returned as a single block
- Eval requires a Groq API key (free tier is enough)

---

## What I'd Improve Next

- Add an Order Context Interpreter agent for malformed or partial JSON inputs
- Test larger top-k (6–8) for conflict cases where multiple policies apply simultaneously
- Replace Groq with a local model via Ollama for fully offline operation
- Add CI with a mock LLM so eval runs without an API key in automated pipelines