import os
import sys
from langchain_ollama import ChatOllama
from modules.vector_store import load_vector_db

def run_rag_system():
    # 1. Load the database we created in ingest.py
    try:
        db = load_vector_db()
    except FileNotFoundError:
        print("❌ Database not found! Please run 'python ingest.py' first.")
        return

    llm = ChatOllama(model="llama3", temperature=0.1)

    while True:
        user_question = input("👉 Ask a question: ").strip()
        
        # Exit conditions
        if user_question.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
        if not user_question:
            continue

        matching_chunks = db.similarity_search(user_question, k=5)

        context_text = ""
        sources_used = set()
        
        for doc in matching_chunks:
            context_text += f"\n--- Content from {doc.metadata.get('source')} ---\n"
            context_text += doc.page_content + "\n"
            sources_used.add(doc.metadata.get('source'))

        
        # 4. Construct a simple, readable text prompt
        full_prompt = f"""
You are a DevOps AI Assistant. Answer the user's question using ONLY the provided context below.
If you cannot find the answer in the context, say "I don't know based on your files."

CONTEXT FROM YOUR FILES:
{context_text}

USER QUESTION: 
{user_question}

ANSWER:
"""

        response = llm.invoke(full_prompt)
        
        print("\n Assistant Answer:")
        print(response.content)
        
        print("\n Files used for this answer:")
        for source in sources_used:
            print(f"  - {source}")
        print("=" * 50 + "\n")

if __name__ == "__main__":
    run_rag_system()