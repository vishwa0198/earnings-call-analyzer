# utils/emb_rag.py
import os
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema import Document
from typing import List, Dict, Any

def get_openai_embeddings():
    """Get OpenAI embeddings instance."""
    return OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))

def check_existing_chroma(persist_directory: str = "./chroma_db") -> bool:
    """Check if ChromaDB already exists with data."""
    return os.path.exists(persist_directory) and os.listdir(persist_directory)

def build_documents_from_chunks(chunks: List[Dict]) -> List[Document]:
    """Convert chunk dictionaries to LangChain Documents."""
    docs = []
    for chunk in chunks:
        content = chunk.get("text", "")
        metadata = {k: v for k, v in chunk.items() if k != "text"}
        docs.append(Document(page_content=content, metadata=metadata))
    return docs

def create_or_load_chroma(docs: List[Document], embeddings, persist_directory: str = "./chroma_db") -> Chroma:
    """Create or load a Chroma vector database."""
    # Check if persist directory exists and has data
    if os.path.exists(persist_directory) and os.listdir(persist_directory):
        # Load existing database
        vectordb = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        try:
            count = vectordb._collection.count()
            print(f"Loaded existing Chroma DB with {count} documents")
        except:
            print("Loaded existing Chroma DB")
    else:
        # Create new database
        vectordb = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory=persist_directory
        )
        vectordb.persist()
        print(f"Created new Chroma DB with {len(docs)} documents")
    
    return vectordb

def run_retrieval_qa(vectordb: Chroma, question: str, top_k: int = 5) -> Dict[str, Any]:
    """Run retrieval-based QA on the vector database."""
    # Create retriever
    retriever = vectordb.as_retriever(search_kwargs={"k": top_k})
    
    # Create LLM
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.0,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Create QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    
    # Use invoke instead of run to handle multiple outputs
    result = qa_chain.invoke({"query": question})
    
    # Format the response
    formatted_result = {
        "answer": result["result"],
        "sources": []
    }
    
    # Format source documents
    for doc in result["source_documents"]:
        formatted_result["sources"].append({
            "page_content": doc.page_content,
            "metadata": doc.metadata
        })
    
    return formatted_result
