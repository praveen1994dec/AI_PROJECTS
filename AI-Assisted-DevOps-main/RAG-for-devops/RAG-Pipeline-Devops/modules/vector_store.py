import os
from typing import List
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


DB_DIR = "chroma_db"
COLLECTION_NAME = "devops_rag_collection"

def get_embedding_model():

    print("Initializing Sentence Transformer Embedding Model...")
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    model_kwargs = {'device': 'cpu'} # Change to 'cuda' if you have a GPU
    encode_kwargs = {'normalize_embeddings': True} # Essential for accurate similarity scoring
    
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

def create_vector_db(chunks: List[Document]) -> Chroma:
    
    if not chunks:
        print("⚠️ No chunks provided to store in the vector database.")
        return None

    embeddings = get_embedding_model()
    print(f"Creating Vector Database at '{DB_DIR}' with {len(chunks)} chunks...")

    # Build and persist the vector store
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=DB_DIR
    )
    
    print(f"✅ Vector Database successfully created and saved to '{DB_DIR}'.")
    return vector_store

def load_vector_db() -> Chroma:
    """
    Loads the already existing local ChromaDB instance for querying.
    """
    if not os.path.exists(DB_DIR):
        raise FileNotFoundError(f"No vector database found at '{DB_DIR}'. Please run ingestion first.")
        
    embeddings = get_embedding_model()
    print(f"Loading existing Vector Database from '{DB_DIR}'...")
    
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=DB_DIR
    )