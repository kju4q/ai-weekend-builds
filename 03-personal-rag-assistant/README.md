# 03 — Personal RAG Assistant with Memory

**Difficulty:** Medium
**Time:** 5-8 hours
**What it does:** A chatbot that knows your documents. Upload PDFs, notes, or any text and chat with them. It remembers past conversations so context builds over time.

## Why build this

You have knowledge scattered everywhere: PDFs, notes, bookmarks, docs. A RAG assistant lets you ask questions across all of it in natural language. The memory layer means it gets better the more you use it.

## What you need

- Python 3.10+
- [LangChain](https://python.langchain.com/) 
- [ChromaDB](https://www.trychroma.com/) (local vector database, no account needed)
- An Anthropic API key or OpenAI API key
- Your documents (PDFs, markdown files, text files)

## Setup (15 minutes)

### 1. Create your project

```bash
mkdir rag-assistant && cd rag-assistant
python -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install langchain langchain-anthropic langchain-community chromadb pypdf tiktoken
```

### 3. Set your API key

```bash
export ANTHROPIC_API_KEY=your_key_here
```

### 4. Create the starter script

Save this as `rag.py`:

```python
import os
from langchain_anthropic import ChatAnthropic
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory

# Load documents from the docs/ folder
def load_documents():
    loaders = []
    docs_path = "./docs"
    
    if not os.path.exists(docs_path):
        os.makedirs(docs_path)
        print("Created docs/ folder. Add your PDFs and text files there.")
        return []
    
    # Load PDFs
    for file in os.listdir(docs_path):
        if file.endswith(".pdf"):
            loaders.append(PyPDFLoader(os.path.join(docs_path, file)))
        elif file.endswith(".txt") or file.endswith(".md"):
            loaders.append(TextLoader(os.path.join(docs_path, file)))
    
    documents = []
    for loader in loaders:
        documents.extend(loader.load())
    
    return documents

# Split documents into chunks
def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    return splitter.split_documents(documents)

# Create vector store
def create_vectorstore(chunks):
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )
    vectorstore = Chroma.from_documents(
        chunks,
        embeddings,
        persist_directory="./chroma_db"
    )
    return vectorstore

# Build the chat chain with memory
def build_chain(vectorstore):
    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        temperature=0.3
    )
    
    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        return_messages=True,
        k=10  # remember last 10 exchanges
    )
    
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
        memory=memory,
        verbose=False
    )
    
    return chain

def main():
    print("Loading documents...")
    documents = load_documents()
    
    if not documents:
        print("No documents found. Add files to the docs/ folder and try again.")
        return
    
    print(f"Loaded {len(documents)} documents")
    
    chunks = split_documents(documents)
    print(f"Split into {len(chunks)} chunks")
    
    vectorstore = create_vectorstore(chunks)
    print("Vector store created")
    
    chain = build_chain(vectorstore)
    print("\nRAG Assistant ready. Type your questions (type 'quit' to exit):\n")
    
    while True:
        question = input("You: ")
        if question.lower() in ["quit", "exit", "q"]:
            break
        
        response = chain.invoke({"question": question})
        print(f"\nAssistant: {response['answer']}\n")

if __name__ == "__main__":
    main()
```

## Try it

### 1. Add your documents

```bash
mkdir docs
# Copy your PDFs, markdown files, or text files into docs/
cp ~/path/to/your/notes.pdf docs/
cp ~/path/to/your/research.md docs/
```

### 2. Run it

```bash
python rag.py
```

### 3. Ask questions

```
You: What are the main points from the research paper?
You: How does this connect to what the other document said about X?
You: Summarize everything I have about agentic workflows
```

The memory means follow-up questions work naturally. It remembers what you just discussed.

## Go deeper

- Add a web interface with Streamlit or Gradio
- Connect to Notion or Google Docs via API so it auto-ingests new documents
- Add source citations so every answer shows which document it came from
- Build a "daily digest" that summarizes what's new across your documents
- Swap ChromaDB for Supabase pgvector for cloud persistence

## What you'll learn

- How RAG (Retrieval Augmented Generation) works end to end
- How vector databases store and retrieve information
- How conversation memory works in LLM applications
- How to build something you'll actually use every day
