from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_documents(documents: List[Document]) -> List[Document]:
    
    print(f"\nSplitting {len(documents)} documents into chunks...")
    
    if not documents:
        print("⚠️ No documents provided to split.")
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400
        chunk_overlap=100
        length_function=len,
        add_start_index=True, # Tracks exactly where the chunk started in the original file
    )

    chunks = splitter.split_documents(documents)
    print(f" Successfully split documents into {len(chunks)} chunks.")
    
    
    return chunks
