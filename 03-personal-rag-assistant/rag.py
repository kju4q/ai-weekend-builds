import os
from langchain_anthropic import ChatAnthropic
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory


def load_documents():
    loaders = []
    docs_path = "./docs"

    if not os.path.exists(docs_path):
        os.makedirs(docs_path)
        print("Created docs/ folder. Add your PDFs and text files there.")
        return []

    for file in os.listdir(docs_path):
        filepath = os.path.join(docs_path, file)
        if file.endswith(".pdf"):
            loaders.append(PyPDFLoader(filepath))
        elif file.endswith(".txt") or file.endswith(".md"):
            loaders.append(TextLoader(filepath))

    documents = []
    for loader in loaders:
        documents.extend(loader.load())

    return documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    return splitter.split_documents(documents)


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


def build_chain(vectorstore):
    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        temperature=0.3
    )

    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        return_messages=True,
        k=10
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
