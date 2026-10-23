from modules.loader import load_devops_documents
from modules.splitter import split_documents
from modules.vector_store import create_vector_db

def main():
    print("  Starting DevOps RAG Ingestion Pipeline  ")
    
    DATA_DIRECTORY = "data"

    # Step 1: Load Documents
    raw_docs = load_devops_documents(DATA_DIRECTORY)
    
    # Step 2: Split Documents
    chunks = split_documents(raw_docs)

    # Step 3: Create Vector Embeddings & Store In DB
    vector_store = create_vector_db(chunks)
    
    if vector_store:
        
        print(" SUCCESS: Vector DB is built and ready!")
    else:
        print("\nIngestion failed during the database creation step.")

if __name__ == "__main__":
    main()