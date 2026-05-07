
# RAG AI ChatBot

## Description
An AI-powered Retrieval-Augmented Generation (RAG) assistant designed to ingest complex PDF documentation and provide highly accurate, context-aware answers. Built to demonstrate production-ready LLM integration, secure authentication, and dual-interface deployment (Web UI + REST API).

## ✨ Features
- 🤖 **AI-Powered Responses:** Utilizes Google Gemini 2.0 Flash for rapid, intelligent generation.
- 📚 **Local RAG Pipeline:** Context retrieval powered by FAISS vector database and Google GenAI embeddings.
- 🌍 **Dynamic Multilingual Support:** Automatic language detection and translation.
- 👥 **Role-Based Access Control (RBAC):** Distinct Admin and User roles.
- 📄 **Dynamic Training:** In-app PDF upload and real-time vector database updating (Admin only).
- 🚀 **Dual Deployment:** Streamlit frontend and Flask REST API backend.

## 🔐 Authentication
- **Secure Local Login:** Werkzeug-hashed credentials managed via `config.yaml`.
- **Google SSO:** One-click OAuth 2.0 authentication with automatic role provisioning.

## Installation & Setup

### Prerequisites
- Python 3.12+
- Google API Key (Google AI Studio)
- Google OAuth Credentials (Optional, for SSO testing)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd rag-chatbot
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Create a `.env` file in the root directory:
```env
# Required: Google Gemini API
GOOGLE_API_KEY="your-gemini-api-key"

# Required: Flask Configuration
FLASK_RUN_HOST="0.0.0.0"
FLASK_RUN_PORT="17191"

# Optional: Google OAuth for SSO
GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your-client-secret"
OAUTH_REDIRECT_URI="http://localhost:8501"
```

### Step 4: Run the Application
Start the Streamlit UI:
```bash
streamlit run main.py
```
*(Access the web interface at `http://localhost:8501`)*

Start the Flask API (in a separate terminal):
```bash
python flaskapp.py
```

## 📦 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Streamlit | Web UI framework |
| **Backend API** | Flask | REST API endpoints |
| **LLM** | Gemini 2.0 Flash | Core generation model |
| **Vector DB** | FAISS | In-memory similarity search |
| **Security** | Werkzeug | Cryptographic password hashing |
| **Data Processing**| PyPDF2 | Document parsing |

## 🔌 API Integration
The Flask API allows external systems to query the RAG knowledge base.

**Endpoint:** `POST http://localhost:17191/chatbot`

**Payload:**
```json
{
  "question": "What is the primary function of the inventory module?",
  "chat_history": []
}
```

## 🛠️ Project Structure
```text
rag-chatbot/
├── docs/                        # Setup documentation
├── static/                      # Web assets
├── flaskapp.py                  # REST API logic
├── main.py                      # Streamlit UI & Auth flow
├── trainapp.py                  # Core RAG & LLM pipeline
├── config.yaml                  # RBAC and hashed credentials
├── requirements.txt             # Dependencies
└── .env                         # Environment variables (Ignored in Git)
```