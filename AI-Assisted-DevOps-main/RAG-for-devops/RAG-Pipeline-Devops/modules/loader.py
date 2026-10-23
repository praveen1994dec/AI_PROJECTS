import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader

def load_devops_documents(data_path: str = "data"):
    """
    Loads all DevOps-related text files from the specified directory.
    """
    print(f"Scanning directory: {data_path}...")
    
    # Check if the directory exists
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"The directory '{data_path}' does not exist. Please create it and add your files.")

    loader = DirectoryLoader(
        data_path,
        glob="**/*",                   # Match all files in all subdirectories
        loader_cls=TextLoader,         # Read everything as plain text
        loader_kwargs={'autodetect_encoding': True}, 
        show_progress=True,            # Show a progress bar in the terminal
        use_multithreading=True        # Speed up loading for large repos
    )

    try:
        documents = loader.load()
        print(f"\n✅ Successfully loaded {len(documents)} documents.")
            
        return documents
        
    except Exception as e:
        print(f"\n❌ Error loading documents: {e}")
        return []
