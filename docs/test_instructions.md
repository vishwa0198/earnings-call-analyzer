# Earnings Call Analyzer - Test Instructions

## Overview

You are tasked with building an **Earnings Call Analyzer** - a comprehensive AI-powered application that processes conference call transcript PDFs to extract insights, generate topics, create summaries, and provide intelligent Q&A capabilities.

**Time for test:** You have 3 days to build this out.

### Expected Deliverable
A **minimalistic but functional application** that demonstrates all three core capabilities outlined below. You may use **any technology stack** you prefer, but the application must showcase the complete functionality described in these instructions.

Refer to this demo video to understand the requirements and flow: https://www.loom.com/share/e23ff0df10cd4290a5954bd441393a77?sid=6755407a-911f-4160-ac44-36bd09a91a5a

**Note**: You are free to use alternative technologies (React, Node.js, OpenAI API, other vector databases, etc.) as long as you implement all required features.

---

## Component 1: PDF Extraction & Processing

### Objective
Extract and structure earnings call transcript data from PDF files into organized, analyzable chunks.

### Key Requirements

#### 1.1 PDF Text Extraction
- **Extract raw text** from PDF using any PDF processing library
- **Identify the conference call start** using pattern matching (phrases like "Ladies and gentlemen, welcome to...")
- **Clean and preprocess** text to remove formatting artifacts

#### 1.2 Metadata Extraction
Extract the following information from the first 1-2 pages:
- **Company name**
- **Conference call date** 
- **Management participants** with their designations

#### 1.3 Section Delineation  
Divide the transcript into distinct sections:

**Opening Remarks Section:**
- Contains management's initial presentation
- Ends when Q&A begins (typically marked by phrases like "first question is from..." from moderator's message)

**Q&A Section:**
- Questions from analysts/investors
- Answers from management
- Use regex patterns to identify section boundaries

#### 1.4 Speaker-Based Chunking
- **Split text by speaker** using speaker name patterns
- **Tag each chunk** with:
  - Speaker name
  - Speaker role (management vs. investor)
  - Section type (opening remarks vs. Q&A)
  - Message content
- **Use fuzzy string matching** to handle speaker name variations

#### 1.5 Q&A Tagging
- **Separate questions from answers** in the Q&A section
- **Match questions to their corresponding answers**
- **Identify speaker companies/roles** for context

---

## Component 2: Topic Extraction & Summarization

### Objective
Use AI to identify key discussion topics from each section and generate business-focused summaries.

### Key Requirements

#### 2.1 Topic Generation
For each section (Opening Remarks and Q&A):
- **Extract 3-5 key topics** using AI/LLM
- Topics should be **business-relevant** (financial performance, strategy, market conditions, etc.)
- **Avoid generic topics** - focus on specific company/industry themes

#### 2.2 AI Prompt Engineering
Design effective prompts that:
- **Understand the context** of earnings calls
- **Focus on financial and strategic content**
- **Generate actionable topic labels**
- **Handle varying content lengths and complexity**

#### 2.3 Topic-Based Summarization
For each identified topic:
- **Generate 2-4 sentence summaries**
- **Include key metrics, data points, and insights**
- **Capture management perspectives and forward-looking statements**
- **Maintain factual accuracy from source content**

#### 2.4 Section-Specific Processing
- **Opening Remarks**: Focus on quarterly performance, strategic updates, financial highlights
- **Q&A Section**: Focus on analyst concerns, management responses, guidance, and outlook

---

## Component 3: FAISS-Powered Intelligent Chatbot

### Objective
Build an intelligent Q&A system that can answer specific questions about the earnings call using semantic search and retrieval-augmented generation (RAG).

### Key Requirements

#### 3.1 Vector Database Setup
- **Use FAISS** (Facebook AI Similarity Search) for vector storage
- **Create embeddings** for all transcript chunks using text embedding models
- **Build searchable index** for semantic similarity matching
- **Support real-time querying** with sub-second response times

#### 3.2 Document Preparation
- **Convert all chunks** (opening remarks, questions, answers) into searchable documents
- **Add metadata** to each chunk:
  - Speaker information
  - Section type (opening remarks vs Q&A)
  - Chunk type (question vs answer)
  - Company/role context
- **Split large chunks** if needed for optimal retrieval

#### 3.3 Semantic Search Implementation
- **Generate query embeddings** for user questions
- **Perform similarity search** to find most relevant chunks (top 5-7)
- **Rank results** by relevance score
- **Return context with source attribution**

#### 3.4 RAG-Based Response Generation
- **Combine retrieved chunks** into context for AI model
- **Generate responses** that:
  - Answer based **only on transcript content**
  - **Cite specific speakers** when possible
  - **Include confidence indicators** based on relevance scores
  - **Handle out-of-scope questions** gracefully
- **Provide source transparency** showing which chunks informed the answer

#### 3.5 Chat Interface Features
- **Conversation history** within session
- **Sample questions** to guide users
- **Source attribution** for each response
- **Confidence scoring** (high/medium/low based on retrieval relevance)
- **Error handling** for failed queries

### Expected Features
- **Real-time responses** (< 3 seconds)
- **Source attribution** showing which transcript sections informed each answer
- **Conversation persistence** during session

---

## Application Integration & UI Requirements

### User Interface Requirements
Create a **minimalistic web interface** that demonstrates all capabilities:

#### Essential UI Components
1. **PDF Upload/Demo Selection**
   - File upload functionality
   - Demo transcript option for immediate testing
   - Processing progress indicators

2. **Section Navigation**
   - Clear separation between Opening Remarks and Q&A
   - Tabbed or sidebar navigation
   - Processing status indicators

3. **Topic & Summary Display**
   - Visual topic cards/lists
   - Expandable summaries
   - Section-specific topic generation
   - Export/download functionality

4. **Interactive Chatbot**
   - Chat interface with message history
   - Sample questions for guidance
   - Source attribution display
   - Confidence indicators

#### Professional Design Requirements
- **Clean, business-focused aesthetics**
- **Responsive design** for different screen sizes
- **Loading states** for AI processing
- **Error messaging** for failed operations
- **Minimal but functional** - focus on demonstrating capabilities

### Technical Architecture
- **Modular design** with separate components for extraction, analysis, and chat
- **Async processing** for better user experience
- **State management** for maintaining processed data
- **Error boundaries** and graceful failure handling

---

## Evaluation Criteria

Your application will be evaluated on:

### Functionality (40%)
- **Complete PDF processing** pipeline
- **Accurate topic extraction** and summarization
- **Working FAISS-based chatbot** with relevant responses
- **Proper error handling** and edge case management

### Code Quality (25%)
- **Clean, readable code** with appropriate comments
- **Modular architecture** with separation of concerns
- **Proper async handling** and performance optimization
- **Following best practices** for your chosen technology stack

### User Experience (20%)
- **Intuitive interface** that showcases all features
- **Smooth workflow** from upload to analysis
- **Professional design** appropriate for business users
- **Clear feedback** and loading states

### Innovation & Technical Depth (15%)
- **Effective use of AI/ML** for topic extraction and chat
- **Optimal vector search** implementation
- **Creative solutions** to technical challenges
- **Performance optimizations**

---

## Submission Requirements

### Deliverables
1. **Complete source code** with clear folder structure
2. **Requirements file** with all dependencies
3. **README.md** with:
   - Setup and installation instructions
   - Environment variable configuration
   - How to run the application
   - Brief technical overview
4. **Demo video** (optional but recommended) showing all features
5. **Live demo** (if deployed) or local setup instructions

### Documentation
- **Code comments** explaining complex logic
- **API documentation** for any custom endpoints
- **Technical decisions** and trade-offs made
- **Known limitations** or areas for improvement

---

## Sample Demo Transcript

A sample earnings call transcript will be provided separately to test your implementation. Your application should be able to process this file and demonstrate all three core capabilities.

### Expected Processing Results
- **Extract company information** and participant details
- **Generate 3-5 relevant topics** for both sections
- **Create business-focused summaries** for each topic
- **Answer questions** about the call content using the chatbot

---

## Additional Notes

### Time Expectations
This is a comprehensive project that should demonstrate full-stack development capabilities. Focus on **working functionality over perfect polish** - a complete, working application is more valuable than a partially finished application with perfect code.

You have 4 days to implement this.

### Technology Flexibility
While we've suggested a specific tech stack, feel free to use technologies you're comfortable with:
- **Frontend**: React, Vue.js, Streamlit, Gradio, or even a simple web interface
- **Backend**: Python, Node.js, Go, or your preferred language
- **AI**: OpenAI API, Azure OpenAI, Anthropic Claude, or other LLM providers
- **Vector DB**: FAISS, Pinecone, Weaviate, or similar

### Success Indicators
A successful implementation should:
- **Process the demo PDF** without errors
- **Generate meaningful topics** relevant to business/finance
- **Provide accurate answers** to questions about the transcript
- **Demonstrate understanding** of RAG architecture and vector search
- **Show clean code practices** and proper documentation

### Questions?
This document should provide all necessary information to build the application. Use your best judgment for implementation details not explicitly specified. The goal is to demonstrate your ability to build AI-powered applications that solve real business problems.

Good luck!
