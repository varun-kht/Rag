# E-Commerce Support Agent — Write-up

## Architecture Overview

The system is orchestrated using **LangChain**, forming a directed graph between 4 agents:

1. **Triage Agent** — Takes the incoming ticket and order context JSON. Classifies the issue type (refund / shipping / payment / promo / fraud / other) and statically checks for missing critical fields. If required info is absent, it generates up to 3 clarifying questions and exits the graph immediately — no vector DB query, no hallucinated assumptions.

2. **Policy Retriever** — Queries the ChromaDB vector store using `sentence-transformers/all-MiniLM-L6-v2` embeddings (local, no API cost). Chunks are split with `RecursiveCharacterTextSplitter` at 500 tokens, 50 token overlap — kept small because policy sections are self-contained; larger overlaps caused duplicate evidence across retrieved chunks. Returns top-k = 4 chunks with doc title and chunk ID as citations.

3. **Resolution Writer Agent** — Drafts a structured response: decision (`approve` / `deny` / `partial` / `escalate`), rationale, verbatim citations from chunk metadata, customer-ready response draft, and internal notes for the support team. Operates strictly on retrieved evidence — no unsupported claims permitted by prompt design.

4. **Compliance / Safety Agent** — Final guardrail before any response is considered complete. Cross-references the Writer's output against retrieved chunks. If it detects a hallucinated claim, missing citation, unapproved action, or sensitive data leak, it forces a rewrite loop back to the Writer with explicit feedback on what rule was broken. Only passes the response when all claims are citation-backed.

## Agent Prompts (High Level)

- **Triage**: *"Given this ticket and order context, classify the issue and identify any missing fields required to resolve it. Do not guess missing values."*
- **Retriever**: *"Retrieve the most relevant policy chunks for this issue type. Return chunk text, document title, and chunk ID. Do not synthesize or interpret — return raw excerpts only."*
- **Writer**: *"Using only the retrieved chunks below, draft a resolution. Every claim must map to a citation. If the chunks do not support a decision, output escalate."*
- **Compliance**: *"Review this draft against the source chunks. Flag any claim not directly supported by a citation. If any unsupported claim exists, return the draft with specific feedback for rewrite."*

## Data Sources

Policy corpus: 12 synthetic markdown files in `src/policies/` representing a comprehensive internal support knowledge base. Covers:
- General return and refund rules
- Strict exceptions (hygiene items, perishables, opened items, final sale)
- Third-party marketplace routing and seller vs first-party rules
- Split shipping and lost package handling
- Regional variance (EU consumer law, California-specific rules)
- Promotions, coupon terms, and dispute handling

All documents are synthetic — authored for this project, no external URLs required.

## Evaluation Summary

Test set: 20 tickets across 4 categories — 8 standard, 6 exception-heavy, 3 conflict, 3 not-in-policy.

| Metric | Result |
|---|---|
| Citation coverage | run `python -m src.eval` |

**Key failure modes observed:**
- The compliance agent occasionally over-escalates when two policies perfectly overlap in priority — for example, when an item is both perishable *and* marketplace-fulfilled. A strict hierarchy explicitly laid out in the writer prompt mitigates this in most cases.
- Ambiguous tickets with partial order context (missing `delivery_date` or `item_category`) sometimes bypass the triage exit when the LLM infers a value rather than flagging it as missing. Fixed by adding explicit null-check logic in the triage prompt.

## What I'd Improve Next

1. **Dynamic re-retrieval** — If the Writer cannot ground a decision in the initial 4 chunks, the graph should loop back to the Retriever with an expanded or rephrased query rather than defaulting to escalation. Currently escalation is the fallback; a second retrieval pass would reduce unnecessary escalations.

2. **Sentiment layer** — A lightweight fast classifier on ticket text to detect high-frustration signals. Would allow the Writer to adjust tone dynamically or trigger auto-escalation before the full pipeline runs.

3. **Larger top-k for conflict cases** — Conflict tickets (region vs seller vs category) consistently benefit from more retrieved chunks. Top-k = 6 or 8 for conflict-classified tickets would give the Writer more policy surface to work with.

4. **Offline eval CI** — Current eval requires a live Groq API key. Replacing the LLM call with a lightweight mock in CI would allow automated regression testing without API costs.