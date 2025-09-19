# utils/faiss_rag.py
import os
import numpy as np
import faiss
import pickle
from typing import List, Dict, Any, Tuple
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
import openai

def get_openai_embeddings():
    """Get OpenAI embeddings instance."""
    return OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))

def create_faiss_index(documents: List[Document], embeddings_model, index_path: str = "./faiss_index") -> faiss.Index:
    """
    Create a FAISS index from documents.
    """
    # Generate embeddings for all documents
    texts = [doc.page_content for doc in documents]
    embeddings = embeddings_model.embed_documents(texts)
    
    # Convert to numpy array
    embeddings_array = np.array(embeddings).astype('float32')
    
    # Create FAISS index
    dimension = embeddings_array.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
    
    # Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings_array)
    
    # Add embeddings to index
    index.add(embeddings_array)
    
    # Save index and metadata
    os.makedirs(index_path, exist_ok=True)
    faiss.write_index(index, f"{index_path}/index.faiss")
    
    # Save document metadata
    metadata = [doc.metadata for doc in documents]
    with open(f"{index_path}/metadata.pkl", "wb") as f:
        pickle.dump(metadata, f)
    
    # Save document contents
    contents = [doc.page_content for doc in documents]
    with open(f"{index_path}/contents.pkl", "wb") as f:
        pickle.dump(contents, f)
    
    print(f"Created FAISS index with {len(documents)} documents")
    return index

def load_faiss_index(index_path: str = "./faiss_index") -> Tuple[faiss.Index, List[Dict], List[str]]:
    """
    Load existing FAISS index and metadata.
    """
    try:
        # Load index
        index = faiss.read_index(f"{index_path}/index.faiss")
        
        # Load metadata
        with open(f"{index_path}/metadata.pkl", "rb") as f:
            metadata = pickle.load(f)
        
        # Load contents
        with open(f"{index_path}/contents.pkl", "rb") as f:
            contents = pickle.load(f)
        
        print(f"Loaded FAISS index with {index.ntotal} documents")
        return index, metadata, contents
    
    except Exception as e:
        print(f"Error loading FAISS index: {e}")
        return None, [], []

def check_existing_faiss(index_path: str = "./faiss_index") -> bool:
    """Check if FAISS index exists."""
    return os.path.exists(f"{index_path}/index.faiss")

def search_faiss_index(index: faiss.Index, metadata: List[Dict], contents: List[str], 
                      query_embedding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search FAISS index for similar documents.
    """
    # Normalize query embedding
    query_embedding = query_embedding.reshape(1, -1).astype('float32')
    faiss.normalize_L2(query_embedding)
    
    # Search
    scores, indices = index.search(query_embedding, top_k)
    
    results = []
    for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
        if idx < len(metadata) and idx < len(contents):
            results.append({
                "page_content": contents[idx],
                "metadata": metadata[idx],
                "score": float(score),
                "rank": i + 1
            })
    
    return results

def run_faiss_retrieval_qa(index: faiss.Index, metadata: List[Dict], contents: List[str], 
                          embeddings_model, question: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Run retrieval-based QA using FAISS.
    """
    # Generate query embedding
    query_embedding = np.array(embeddings_model.embed_query(question)).astype('float32')
    
    # Search for relevant documents
    search_results = search_faiss_index(index, metadata, contents, query_embedding, top_k)
    
    # Prepare context for LLM
    context = "\n\n".join([result["page_content"] for result in search_results])
    
    # Generate answer using OpenAI
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompt = f"""
    Based on the following context from an earnings call transcript, answer the question.
    
    Context:
    {context}
    
    Question: {question}
    
    Instructions:
    - Answer based ONLY on the provided context
    - Cite specific speakers when possible
    - Include relevant metrics and data points
    - If the answer is not in the context, say so clearly
    - Be concise but comprehensive
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a financial analyst expert at answering questions about earnings call transcripts. Always base your answers on the provided context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Calculate confidence based on relevance scores
        avg_score = np.mean([result["score"] for result in search_results])
        if avg_score > 0.8:
            confidence = "High"
        elif avg_score > 0.6:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        return {
            "answer": answer,
            "sources": search_results,
            "confidence": confidence,
            "avg_relevance_score": float(avg_score)
        }
    
    except Exception as e:
        print(f"Error generating answer: {e}")
        return {
            "answer": "Sorry, I couldn't generate an answer at this time.",
            "sources": search_results,
            "confidence": "Low",
            "avg_relevance_score": 0.0
        }

def clear_faiss_index(index_path: str = "./faiss_index"):
    """Clear FAISS index and related files."""
    import shutil
    try:
        if os.path.exists(index_path):
            shutil.rmtree(index_path)
            print("FAISS index cleared successfully")
            return True
    except Exception as e:
        print(f"Error clearing FAISS index: {e}")
        return False
