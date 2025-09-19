# Earnings Call Analyzer

A comprehensive AI-powered application for analyzing earnings call transcripts with intelligent topic extraction, summarization, and interactive Q&A capabilities.

## Features

### 🔍 PDF Processing & Extraction
- **Advanced PDF text extraction** with cleaning and preprocessing
- **Conference call start detection** using pattern matching
- **Metadata extraction** (company name, date, participants)
- **Section delineation** (Opening Remarks vs Q&A)
- **Speaker-based chunking** with fuzzy matching for role detection

### 🤖 AI-Powered Analysis
- **Topic extraction** using OpenAI GPT-4 for both sections
- **Business-focused summaries** with key metrics and insights
- **Intelligent Q&A pairing** with context extraction
- **Speaker role classification** (management vs investor)

### 💬 Interactive Chat System
- **FAISS-powered semantic search** for sub-second response times
- **Retrieval-Augmented Generation (RAG)** for accurate answers
- **Source attribution** with relevance scoring
- **Conversation history** within session
- **Confidence indicators** (High/Medium/Low)

### 📊 Comprehensive UI
- **Tabbed interface** for organized navigation
- **Topic visualization** with expandable summaries
- **Sample questions** for guidance
- **Company information** display
- **Q&A analysis** tools

## Installation

### Prerequisites
- Python 3.8 or higher
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd earnings-call-analyzer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirement.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

## Usage

### 1. Upload Transcript
- Upload a PDF earnings call transcript
- Or use the demo file (Q2FY24 Laurus Labs transcript)

### 2. Processing
The application will automatically:
- Extract and clean text from the PDF
- Identify conference call start
- Extract company metadata and participants
- Split into Opening Remarks and Q&A sections
- Process speaker chunks with role detection
- Generate AI-powered topics and summaries
- Create FAISS vector index for search

### 3. Explore Results
- **Topics & Summary Tab**: View extracted topics with AI-generated summaries
- **Chat Tab**: Ask questions about the transcript with sample questions
- **Company Info Tab**: View extracted metadata and participants
- **Q&A Analysis Tab**: Analyze section lengths and content

### 4. Interactive Chat
- Ask specific questions about the earnings call
- Get answers with source attribution
- View conversation history
- See confidence levels for responses

## Technical Architecture

### Components

1. **PDF Processing** (`utils/pdf_utils.py`)
   - Text extraction with PyPDF2
   - Text cleaning and preprocessing
   - Conference call start detection
   - Participant extraction

2. **Text Parsing** (`utils/parser.py`)
   - Speaker chunking with fuzzy matching
   - Q&A section detection
   - Role classification
   - Question-answer pairing

3. **Topic Extraction** (`utils/topic_extractor.py`)
   - AI-powered topic generation
   - Business-focused summarization
   - Section-specific processing

4. **Vector Search** (`utils/faiss_rag.py`)
   - FAISS index creation and management
   - Semantic search implementation
   - RAG-based response generation

5. **Web Interface** (`app.py`)
   - Streamlit-based UI
   - Session state management
   - Tabbed navigation
   - Real-time processing

### Key Technologies

- **Streamlit**: Web interface framework
- **OpenAI GPT-4**: AI for topic extraction and summarization
- **FAISS**: Vector database for semantic search
- **PyPDF2**: PDF text extraction
- **RapidFuzz**: Fuzzy string matching for speaker names
- **LangChain**: Document processing and embeddings

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for AI features

### Customization
- Modify topic extraction prompts in `utils/topic_extractor.py`
- Adjust speaker detection patterns in `utils/parser.py`
- Customize UI components in `app.py`

## Performance

- **Processing Time**: 30-60 seconds for typical earnings call
- **Search Response**: < 3 seconds for queries
- **Memory Usage**: ~500MB for typical transcript
- **Storage**: FAISS index stored locally

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**
   - Ensure `.env` file exists with valid API key
   - Check API key permissions and billing

2. **PDF Processing Issues**
   - Ensure PDF is text-based (not scanned image)
   - Try different PDF files if extraction fails

3. **Memory Issues**
   - Clear database using "Clear Database" button
   - Restart application if needed

4. **Slow Performance**
   - Reduce top_k parameter in search
   - Use smaller text chunks

## File Structure

```
earnings-call-analyzer/
├── app.py                 # Main Streamlit application
├── requirement.txt        # Python dependencies
├── README.md             # This file
├── .env                  # Environment variables (create this)
├── docs/                 # Sample transcripts
│   └── Q2FY24_LaurusLabs_EarningsCallTranscript.pdf
└── utils/                # Utility modules
    ├── __init__.py
    ├── pdf_utils.py      # PDF processing
    ├── parser.py         # Text parsing and chunking
    ├── topic_extractor.py # AI topic extraction
    └── faiss_rag.py      # Vector search and RAG
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the code comments
3. Open an issue on GitHub

## Future Enhancements

- [ ] Support for multiple transcript formats
- [ ] Advanced analytics and visualizations
- [ ] Export functionality for reports
- [ ] Multi-language support
- [ ] Real-time transcript processing
- [ ] Integration with financial data APIs
