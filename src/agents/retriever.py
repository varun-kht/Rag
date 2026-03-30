import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from src.models import TicketState

CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")

def retriever_node(state: TicketState) -> TicketState:
    print("--- POLICY RETRIEVER AGENT ---")
    
    # If there's missing critical info, we might skip heavy retrieval, but let's do it anyway just in case.
    if state.get("missing_critical_info") and state.get("clarifying_questions"):
        print("Missing critical info detected, skipping extensive retrieval.")
        return {"retrieved_chunks": []}

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    if not os.path.exists(CHROMA_DIR):
        print("WARNING: ChromaDB directory not found. Have you run ingest.py?")
        return {"retrieved_chunks": []}
        
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR, 
        embedding_function=embeddings
    )
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    
    # Construct a search query that includes the classification and the ticket text
    query = f"Issue: {state['classification']}\nTicket: {state['ticket_text']}"
    
    docs = retriever.invoke(query)
    
    chunks = []
    for doc in docs:
        chunks.append({
            "content": doc.page_content,
            "metadata": doc.metadata
        })
        
    print(f"Retrieved {len(chunks)} chunks.")
    return {"retrieved_chunks": chunks}
