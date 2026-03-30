import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

POLICIES_DIR = os.path.join(os.path.dirname(__file__), "policies")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")

def ingest_docs():
    print(f"Loading documents from {POLICIES_DIR}...")
    loader = DirectoryLoader(POLICIES_DIR, glob="**/*.md", loader_cls=TextLoader)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n### ", "\n## ", "\n\n", "\n", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    
    # Add unique chunk IDs to metadata
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = f"chunk_{i}"
        
        # Extract title from the markdown content (heuristic: first line if starts with #)
        first_line = chunk.page_content.split('\n')[0]
        if first_line.startswith('# '):
            chunk.metadata["title"] = first_line.replace('# ', '').strip()
        else:
            chunk.metadata["title"] = os.path.basename(chunk.metadata["source"])

    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    print("Initializing HuggingFace Embeddings (all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Clear existing vectorstore if any
    if os.path.exists(CHROMA_DIR):
        print(f"Clearing existing vectorstore at {CHROMA_DIR}...")
        import shutil
        shutil.rmtree(CHROMA_DIR, ignore_errors=True)

    print("Creating vector store...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )
    print("Ingestion complete!")

if __name__ == "__main__":
    ingest_docs()
