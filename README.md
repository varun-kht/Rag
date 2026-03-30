# E-commerce Support Resolution Agent

A multi-agent Retrieval-Augmented Generation (RAG) system built with **LangGraph** to autonomously process and resolve customer support tickets based on strict e-commerce policy documents.

## Core Features
- **4 Dedicated Agents**: Triage, Policy Retriever, Resolution Writer, and Compliance/Safety.
- **Strict Grounding**: The Writer and Compliance agents strictly adhere to retrieved snippets, reducing hallucinations.
- **Auto-Correction**: The Compliance agent reviews the drafted response before it is seen by the customer, forcing rewrites if citations are missing or if claims are unsupported.
- **Edge-Case Handling**: Detects missing information, conflicts, out-of-policy demands, and handles exceptions automatically.

## Setup Instructions

1. **Clone or Download the Repository**
2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment Variables**:
   Copy `.env.example` to `.env` and configure your API key. By default, this uses Groq via `langchain-groq`.
   ```bash
   GROQ_API_KEY=your_api_key_here
   ```

## Running the System

### 1. Ingest Documents
First, build the ChromaDB vector store by embedding the synthetic policy documents. It uses a local `HuggingFaceEmbeddings` model (`all-MiniLM-L6-v2`) to cut down on API costs.
```bash
python src/ingest.py
```

### 2. Run the Evaluation Suite
Evaluates the system against 20 test cases (Standard, Exception, Conflict, Not-in-policy).
```bash
python src/eval.py
```
The script will output metrics and dump the traces to `eval_results.json`.

### 3. Interactive CLI
To test a single ticket interactively, run:
```bash
python src/main.py
```
