# app.py
import os
import streamlit as st
from utils.pdf_utils import extract_text_from_pdf_bytes, get_first_pages_text_from_bytes, find_conference_call_start, extract_participants_from_first_pages
from utils.parser import extract_company_name, extract_date, find_q_a_split, basic_speaker_chunks, map_speakers_to_roles, pair_questions_answers
from utils.faiss_rag import get_openai_embeddings, create_faiss_index, load_faiss_index, check_existing_faiss, run_faiss_retrieval_qa, clear_faiss_index
from utils.topic_extractor import process_section_topics
from langchain.schema import Document
from typing import List, Dict
from dotenv import load_dotenv
import shutil
import time
import gc

# Load variables from .env file
load_dotenv()

st.set_page_config(page_title="Earnings Call Analyzer", layout="wide")
st.title("Earnings Call Analyzer")

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    st.error("OPENAI_API_KEY not set in environment. Please set it before running.")
    st.stop()

# Initialize session state
if "faiss_index" not in st.session_state:
    st.session_state.faiss_index = None
if "faiss_metadata" not in st.session_state:
    st.session_state.faiss_metadata = []
if "faiss_contents" not in st.session_state:
    st.session_state.faiss_contents = []
if "processed" not in st.session_state:
    st.session_state.processed = False
if "company" not in st.session_state:
    st.session_state.company = "Unknown"
if "call_date" not in st.session_state:
    st.session_state.call_date = "Unknown"
if "participants" not in st.session_state:
    st.session_state.participants = []
if "opening_topics" not in st.session_state:
    st.session_state.opening_topics = []
if "qa_topics" not in st.session_state:
    st.session_state.qa_topics = []
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "clear_requested" not in st.session_state:
    st.session_state.clear_requested = False

def force_delete_directory(path, max_attempts=5):
    """Force delete directory with multiple attempts for Windows file locking"""
    for attempt in range(max_attempts):
        try:
            if os.path.exists(path):
                # Try to make all files writable
                for root, dirs, files in os.walk(path):
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            os.chmod(file_path, 0o777)
                        except:
                            pass
                
                shutil.rmtree(path)
                return True
        except PermissionError:
            if attempt < max_attempts - 1:
                time.sleep(0.5 * (attempt + 1))  # Increasing delay
                gc.collect()  # Force garbage collection
            else:
                return False
    return False

def clear_database():
    """Safely clear the FAISS database"""
    try:
        # Step 1: Clear FAISS index
        success = clear_faiss_index()
        
        # Step 2: Clear all caches
        st.cache_resource.clear()
        
        # Step 3: Force garbage collection
        gc.collect()
        
        # Step 4: Wait for file handles to be released
        time.sleep(1)
        
        # Step 5: Reset session state
        st.session_state.processed = False
        st.session_state.company = "Unknown"
        st.session_state.call_date = "Unknown"
        st.session_state.participants = []
        st.session_state.opening_topics = []
        st.session_state.qa_topics = []
        st.session_state.conversation_history = []
        st.session_state.faiss_index = None
        st.session_state.faiss_metadata = []
        st.session_state.faiss_contents = []
        st.session_state.clear_requested = False
        
        if success:
            return True
        else:
            return "partial"
            
    except Exception as e:
        st.error(f"Error clearing database: {str(e)}")
        return False

# Check for existing FAISS index on startup
@st.cache_resource
def load_existing_faiss():
    """Load existing FAISS index if it exists"""
    if check_existing_faiss():
        index, metadata, contents = load_faiss_index()
        return index, metadata, contents
    return None, [], []

# Handle clear database request
if st.session_state.clear_requested:
    with st.spinner("Clearing database..."):
        result = clear_database()
        if result == True:
            st.success("Database cleared successfully!")
        elif result == "partial":
            st.warning("Database cleared from memory. Some files may remain but will be overwritten.")
        else:
            st.error("Could not fully clear database files. Try restarting the application.")
        time.sleep(1)
        st.rerun()

# Auto-load existing database (only if not clearing)
if not st.session_state.processed and st.session_state.faiss_index is None and not st.session_state.clear_requested:
    existing_index, existing_metadata, existing_contents = load_existing_faiss()
    if existing_index is not None:
        st.session_state.faiss_index = existing_index
        st.session_state.faiss_metadata = existing_metadata
        st.session_state.faiss_contents = existing_contents
        st.session_state.processed = True
        
        # Load metadata from file
        metadata_file = "./faiss_index/metadata.txt"
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, "r") as f:
                    lines = f.readlines()
                    if len(lines) >= 2:
                        st.session_state.company = lines[0].strip()
                        st.session_state.call_date = lines[1].strip()
            except:
                pass
        st.success("Existing transcript database loaded automatically!")

with st.sidebar:
    st.header("Upload Transcript")
    
    if st.session_state.processed:
        st.success("Transcript Ready")
        st.write(f"Company: {st.session_state.company}")
        st.write(f"Date: {st.session_state.call_date}")
        
        if st.button("Clear Database", type="secondary"):
            st.session_state.clear_requested = True
            st.rerun()
        
        st.divider()
    
    uploaded = st.file_uploader("Upload PDF", type=["pdf"])
    use_demo = st.checkbox("Use demo file")
    process_btn = st.button("Process")

if process_btn:
    if not uploaded and not use_demo:
        st.sidebar.error("Upload a PDF or select demo.")
    else:
        with st.spinner("Processing transcript..."):
            # Clear any existing database first
            if st.session_state.faiss_index is not None:
                clear_database()
            
            if use_demo:
                demo_path = "docs/Q2FY24_LaurusLabs_EarningsCallTranscript.pdf"
                with open(demo_path, "rb") as f:
                    file_bytes = f.read()
            else:
                file_bytes = uploaded.read()

            # Extract and clean text
            full_text = extract_text_from_pdf_bytes(file_bytes)
            first_pages = get_first_pages_text_from_bytes(file_bytes, n=2)
            
            # Find conference call start
            call_start = find_conference_call_start(full_text)
            if call_start > 0:
                full_text = full_text[call_start:]

            # Extract metadata
            company = extract_company_name(first_pages)
            call_date = extract_date(first_pages)
            participants = extract_participants_from_first_pages(first_pages)
            
            # Split into sections
            opening_text, qa_text = find_q_a_split(full_text)

            # Update session state
            st.session_state.company = company
            st.session_state.call_date = str(call_date) if call_date else "Unknown"
            st.session_state.participants = participants
            st.session_state.opening_text = opening_text
            st.session_state.qa_text = qa_text

            opening_chunks_raw = basic_speaker_chunks(opening_text)
            qa_chunks_raw = basic_speaker_chunks(qa_text)

            # Create participant list for role mapping
            participant_list = [p['name'] for p in participants]

            opening_mapped = map_speakers_to_roles(opening_chunks_raw, participant_list)
            qa_mapped = map_speakers_to_roles(qa_chunks_raw, participant_list)

            # Add section tags
            for o in opening_mapped:
                o["section"] = "opening_remarks"
            for q in qa_mapped:
                q["section"] = "qa"

            # Pair Q&A
            qa_pairs = pair_questions_answers(qa_mapped)

            # Create documents for FAISS
            all_chunks = opening_mapped + qa_mapped
            docs = []
            for chunk in all_chunks:
                content = chunk.get("text", "")
                metadata = {k: v for k, v in chunk.items() if k != "text"}
                docs.append(Document(page_content=content, metadata=metadata))

            # Create FAISS index
            embeddings = get_openai_embeddings()
            faiss_index = create_faiss_index(docs, embeddings)
            
            # Update session state
            st.session_state.faiss_index = faiss_index
            st.session_state.faiss_metadata = [doc.metadata for doc in docs]
            st.session_state.faiss_contents = [doc.page_content for doc in docs]
            st.session_state.processed = True
            
            # Extract topics using AI
            with st.spinner("Extracting topics and generating summaries..."):
                opening_topics = process_section_topics(opening_text, "opening_remarks", company)
                qa_topics = process_section_topics(qa_text, "qa", company)
                
                st.session_state.opening_topics = opening_topics
                st.session_state.qa_topics = qa_topics
            
            # Save metadata
            try:
                os.makedirs("./faiss_index", exist_ok=True)
                with open("./faiss_index/metadata.txt", "w") as f:
                    f.write(f"{st.session_state.company}\n")
                    f.write(f"{st.session_state.call_date}\n")
            except:
                pass
            
            st.success("Processing complete!")

# Main content
if not st.session_state.processed:
    st.info("Upload and process a transcript to get started.")
else:
    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Topics & Summary", "💬 Chat", "📋 Company Info", "📈 Q&A Analysis"])
    
    with tab1:
        st.header("Topics & Summary")
        
        # Opening Remarks Topics
        if st.session_state.opening_topics:
            st.subheader("🎯 Opening Remarks Topics")
            opening_data = st.session_state.opening_topics
            for i, topic in enumerate(opening_data.get("topics", []), 1):
                with st.expander(f"{i}. {topic.get('topic', 'Unknown Topic')}"):
                    st.write(f"**Description:** {topic.get('description', 'No description available')}")
                    st.write(f"**Summary:** {topic.get('summary', 'No summary available')}")
        
        st.divider()
        
        # Q&A Topics
        if st.session_state.qa_topics:
            st.subheader("❓ Q&A Section Topics")
            qa_data = st.session_state.qa_topics
            for i, topic in enumerate(qa_data.get("topics", []), 1):
                with st.expander(f"{i}. {topic.get('topic', 'Unknown Topic')}"):
                    st.write(f"**Description:** {topic.get('description', 'No description available')}")
                    st.write(f"**Summary:** {topic.get('summary', 'No summary available')}")
    
    with tab2:
        st.header("💬 Interactive Chat")
        
        # Sample questions
        st.subheader("Sample Questions")
        sample_questions = [
            "What were the key financial highlights?",
            "What is the company's outlook for next quarter?",
            "What challenges did management discuss?",
            "What strategic initiatives were mentioned?",
            "What was the revenue growth rate?"
        ]
        
        cols = st.columns(2)
        for i, question in enumerate(sample_questions):
            with cols[i % 2]:
                if st.button(f"💡 {question}", key=f"sample_{i}"):
                    st.session_state.current_query = question
        
        # Chat interface
        st.subheader("Ask a Question")
        query = st.text_input("Enter your question:", 
                             value=st.session_state.get("current_query", ""), 
                             placeholder="What were the key financial highlights?")
        
        if st.button("Ask", type="primary"):
            if query:
                with st.spinner("Generating answer..."):
                    result = run_faiss_retrieval_qa(
                        st.session_state.faiss_index,
                        st.session_state.faiss_metadata,
                        st.session_state.faiss_contents,
                        get_openai_embeddings(),
                        query,
                        top_k=5
                    )
                    
                    # Add to conversation history
                    st.session_state.conversation_history.append({
                        "question": query,
                        "answer": result["answer"],
                        "confidence": result["confidence"],
                        "sources": result["sources"]
                    })
                    
                    # Display answer
                    st.write("**Answer:**")
                    st.write(result["answer"])
                    
                    # Confidence indicator
                    confidence_color = "green" if result["confidence"] == "High" else "orange" if result["confidence"] == "Medium" else "red"
                    st.markdown(f"**Confidence:** :{confidence_color}[{result['confidence']}]")
                    
                    # Sources
                    with st.expander("View Sources"):
                        for i, source in enumerate(result["sources"], 1):
                            meta = source.get("metadata", {})
                            st.write(f"**Source {i}:**")
                            st.write(f"Speaker: {meta.get('speaker_name', 'Unknown')} | Role: {meta.get('role', 'Unknown')} | Section: {meta.get('section', 'Unknown')}")
                            st.write(f"Relevance Score: {source.get('score', 0):.3f}")
                            st.write(source.get("page_content", "")[:400] + "...")
                            st.divider()
            else:
                st.warning("Please enter a question.")
        
        # Conversation history
        if st.session_state.conversation_history:
            st.subheader("Conversation History")
            for i, conv in enumerate(reversed(st.session_state.conversation_history[-5:]), 1):
                with st.expander(f"Q{i}: {conv['question'][:50]}..."):
                    st.write(f"**Question:** {conv['question']}")
                    st.write(f"**Answer:** {conv['answer']}")
                    st.write(f"**Confidence:** {conv['confidence']}")
    
    with tab3:
        st.header("📋 Company Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Basic Info")
            st.write(f"**Company:** {st.session_state.company}")
            st.write(f"**Call Date:** {st.session_state.call_date}")
            st.write(f"**Total Documents:** {len(st.session_state.faiss_contents)}")
        
        with col2:
            st.subheader("Participants")
            if st.session_state.participants:
                for participant in st.session_state.participants:
                    st.write(f"• **{participant.get('name', 'Unknown')}** - {participant.get('title', 'Unknown Title')}")
            else:
                st.write("No participants identified")
    
    with tab4:
        st.header("📈 Q&A Analysis")
        
        if hasattr(st.session_state, 'opening_text') and hasattr(st.session_state, 'qa_text'):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Opening Remarks")
                st.write(f"**Length:** {len(st.session_state.opening_text)} characters")
                st.write(f"**Estimated Duration:** {len(st.session_state.opening_text) // 200} minutes")
                
                if st.button("View Opening Remarks"):
                    st.text_area("Opening Remarks Content", st.session_state.opening_text, height=300)
            
            with col2:
                st.subheader("Q&A Section")
                st.write(f"**Length:** {len(st.session_state.qa_text)} characters")
                st.write(f"**Estimated Duration:** {len(st.session_state.qa_text) // 200} minutes")
                
                if st.button("View Q&A Content"):
                    st.text_area("Q&A Content", st.session_state.qa_text, height=300)
