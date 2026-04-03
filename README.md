# HR Copilot - Career Assistant

A unified AI-powered system for employee career development and HR policy assistance using **Groq LLM** and **FAISS vector database**.

## Features

- **Career Learning Assistant**: Analyzes skill gaps, generates personalized learning roadmaps, and provides career path recommendations
- **HR Policy Chat**: Query HR policies with RAG (Retrieval-Augmented Generation) for accurate, confidence-scored responses
- **Dual System Integration**: Both systems operate seamlessly within a single Streamlit interface
- **Advanced RAG Pipeline**: Utilizes FAISS embeddings with reranking for improved retrieval accuracy

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI, Uvicorn
- **LLM**: Groq API
- **Vector DB**: FAISS with Sentence Transformers
- **Python**: 3.10+

## Quick Start

### Prerequisites
- Python 3.10 or higher
- Groq API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Vishnuvaradhan-M/HR-copilot_Career_Assistant.git
cd HR-copilot
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
# or
source .venv/bin/activate  # macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file with your Groq API key:
```
GROQ_API_KEY=your_groq_api_key_here
UPLOAD_DIR=./uploads
```

### Running the Application

#### Option 1: Streamlit UI (Recommended)
```bash
streamlit run streamlit_app.py
```

#### Option 2: Using PowerShell Scripts (Windows)
```powershell
# Start the app
.\start_streamlit.ps1

# Stop the app
.\stop_streamlit.ps1
```

#### Option 3: FastAPI Backend
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Project Structure

```
.
├── streamlit_app.py           # Main Streamlit UI
├── requirements.txt           # Python dependencies
├── app/
│   ├── main.py               # FastAPI backend
│   ├── career_assistant.py   # Career analysis logic
│   ├── hr_policy_chat.py     # HR policy RAG system
│   ├── faiss_store.py        # Vector database operations
│   ├── retriever.py          # RAG retriever with reranking
│   ├── ingest.py             # Document processing
│   ├── models.py             # Data models and SQLite
│   ├── ui_components.py      # Streamlit UI components
│   ├── reranker.py           # Cross-encoder reranking
│   ├── rag_logger.py         # RAG logging utilities
│   ├── prompts/
│   │   └── career_prompts.py # Career assistant prompts
│   └── schemas/
│       └── career.py         # Data schema definitions
├── uploads/                  # Document upload directory
├── faiss_index.index        # FAISS vector index
└── .env                      # Environment configuration
```

## Key Components

### Career Assistant
- Normalizes job roles using cached role mappings
- Analyzes skill gaps between current and target roles
- Generates learning timelines with recommended resources
- Provides proficiency level assessments

### HR Policy Chat
- Retrieves relevant policies using FAISS vector search
- Reranks results for improved accuracy
- Provides confidence scores for answers
- Includes evidence chunks from source documents

## Configuration

Key environment variables:
- `GROQ_API_KEY`: Your Groq API key (required)
- `UPLOAD_DIR`: Directory for document uploads (default: `./uploads`)

## Performance Notes

- Initial request may take longer due to model loading
- Reranker loads on-demand for improved efficiency
- FAISS index is pre-built and optimized


## License

MIT License - See LICENSE file for details

## Contact

For questions or support, please open an issue on GitHub.
