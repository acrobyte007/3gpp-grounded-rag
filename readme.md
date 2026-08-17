# RAG API - Document Q&A System

A production-ready **RAG (Retrieval-Augmented Generation)** API built with FastAPI, LangChain, and Pinecone for intelligent document querying with hybrid search capabilities.

## 🚀 Features

- **Document Ingestion**: Upload and process PDF, DOCX, and TXT documents
- **Hybrid Search**: Vector similarity search combined with BM25 reranking
- **Intelligent Q&A**: Natural language question answering using Mistral AI
- **Multi-User Isolation**: Separate namespaces per user in Pinecone
- **Authentication**: JWT-based user authentication with Argon2 password hashing
- **Conversation Memory**: Track conversation history per session
- **Secure Middleware**: PII detection, rate limiting, and retry mechanisms

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph "Client Layer"
        A[Web/Mobile Client]
    end
    subgraph "API Layer"
        B[FastAPI Server]
        C[Auth Routes]
        D[Ingestion Routes]
        E[Chat Routes]
        F[Document Routes]
    end
    subgraph "Agent Layer"
        G[RAG Agent Manager]
        H[Search Tool]
        I[BM25 Reranker]
        J[Middleware]
    end
    subgraph "Service Layer"
        K[Embedding Service]
        L[Keyword Extractor]
        M[File Storage Service]
    end
    subgraph "Storage Layer"
        N[PostgreSQL]
        O[Pinecone Vector DB]
        P[Filebase/S3]
    end
    A --> B
    B --> C
    B --> D
    B --> E
    B --> F
   
    E --> G
    G --> H
    H --> K
    H --> I
    G --> J
   
    D --> M
    D --> N
    D --> O
   
    E --> N
    E --> O
   
    M --> P
    K --> O
    H --> O
```

## 🔄 Agent & Tool Architecture

```mermaid
graph TD
    subgraph "RAG Agent"
        A[User Query + Doc IDs] --> B[RAG Agent Manager]
        B --> C{Validate Input}
        C -->|Invalid| D[Return Error]
        C -->|Valid| E[LLM: Mistral AI]
        E --> F[Tool: Search]
       
        subgraph "Middleware"
            M1[PII Middleware<br/>- Email Redaction<br/>- Credit Card Masking<br/>- API Key Blocking]
            M2[Summarization Middleware]
            M3[Call Limit Middleware]
            M4[Retry Middleware]
        end
       
        E --> M1
        M1 --> M2
        M2 --> M3
        M3 --> M4
        M4 --> F
    end
   
    subgraph "Tool: Search"
        F --> G[Vector Search<br/>top_k=30]
        G --> H[Pinecone DB]
        H --> I[Get 30 Chunks<br/>with Tokens]
        I --> J[BM25 Reranker]
        J --> K[Score & Rerank]
        K --> L[Return Top 10 Chunks]
        L --> M[LLM Generates Answer]
        M --> N[Return Answer to User]
    end
    subgraph "Data Flow"
        P[UserContext<br/>- namespace: user_id<br/>- doc_ids: List[str]] --> F
        Q[Query Tokens<br/>via tokenize_sentences] --> J
        R[Chunks with<br/>- text<br/>- tokens<br/>- metadata] --> J
    end
    style A fill:#e1f5fe
    style N fill:#c8e6c9
    style D fill:#ffcdd2
    style F fill:#fff3e0
    style J fill:#f3e5f5
```

## 📁 Project Structure

bash```
app/
├── agent/
│   ├── __init__.py
│   ├── agent.py              # RAG Agent Manager
│   ├── tools.py              # Search Tool with BM25
│   ├── schemas.py            # Pydantic schemas
│   ├── exceptions.py         # Custom exceptions
│   ├── system_prompt.py      # System prompt for LLM
│   ├── llm_client.py         # Mistral LLM client
│   └── guards.py             # Middleware configuration
├── routes/
│   ├── auth.py               # Authentication routes
│   ├── ingestion.py          # Document upload routes
│   ├── chat.py               # Chat/QA routes
│   └── documents.py          # Document CRUD routes
├── services/
│   ├── embeddings.py         # Embedding service (Google Gemini)
│   ├── keyword_extraction.py # YAKE keyword extraction
│   ├── filebase.py           # Filebase/S3 storage
│   ├── extraction.py         # Document text extraction
│   └── cleaning_chunking.py  # Text cleaning & chunking
├── database/
│   ├── database.py           # Database connection manager
│   ├── models.py             # SQLAlchemy models
│   ├── repositories.py       # Database repositories
│   └── pincone_db.py         # Pinecone vector database
└── logger/
    └── logger.py             # Logging configuration
bash```

## 🛠️ Technology Stack

### Core Technologies

- **FastAPI** – Web framework
- **LangChain** – LLM framework and agent orchestration
- **Mistral AI** – Primary LLM for answer generation
- **Google Gemini** – Embeddings model
- **Pinecone** – Vector database
- **PostgreSQL** – Relational database
- **Filebase/S3** – Document storage

### Key Libraries

- **Authentication**: `python-jose`, `passlib[argon2]`
- **Document Processing**: `PyPDF2`, `python-docx`, `pdfplumber`
- **Keyword Extraction**: `YAKE`
- **Vector Operations**: `numpy`
- **HTTP Client**: `httpx`

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Pinecone account
- Mistral AI API key
- Google AI API key
- Filebase/S3 account

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/rag-api.git
cd rag-api
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt:**

```txt
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
sqlalchemy==2.0.23
asyncpg==0.29.0
psycopg2-binary==2.9.9
python-jose[cryptography]==3.3.0
passlib[argon2]==1.7.4
python-dotenv==1.0.0
python-docx==1.1.0
PyPDF2==3.0.1
pdfplumber==0.10.3
yake==0.4.8
numpy==1.26.2
langchain==0.1.0
langchain-mistralai==0.0.3
langgraph==0.0.22
langsmith==0.0.87
google-generativeai==0.3.0
pinecone-client==2.2.4
boto3==1.34.6
requests==2.31.0
aiofiles==23.2.1
```

### 4. Configure Environment Variables

Create a `.env` file:

```env
# Database
DB_URL=postgresql+asyncpg://user:password@localhost:5432/rag_db

# Authentication
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Pinecone
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-environment
PINECONE_INDEX_NAME=rag-index
EMBEDDING_DIMENSION=768
PINECONE_METRIC=cosine

# Mistral AI
MISTRAL_API_KEY=your-mistral-api-key
MISTRAL_MODEL=ministral-8b-latest
MISTRAL_TEMPERATURE=0.7
MISTRAL_MAX_RETRIES=2

# Google Gemini
GOOGLE_API_KEY=your-google-api-key

# Filebase/S3
FILEBASE_ENDPOINT=your-filebase-endpoint
FILEBASE_ACCESS_TOKEN=your-access-token
FILEBASE_SECRET_ACCESS_KEY=your-secret-key
FILEBASE_BUCKET_NAME=your-bucket-name
```

### 5. Initialize Database

```bash
python -m app.database.database
```

### 6. Create Pinecone Index

```python
from pinecone import Pinecone, ServerlessSpec
import os

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

pc.create_index(
    name=os.getenv("PINECONE_INDEX_NAME"),
    dimension=768,
    metric="cosine",
    spec=ServerlessSpec(
        cloud="aws",
        region="us-west-2"
    )
)
```

## 🚀 Running the Application

### Development

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 API Documentation

Once running, access the automatic API documentation:

- **Swagger UI**: <http://localhost:8000/docs>

### API Endpoints

#### Authentication

| Method | Endpoint          | Description                  |
|--------|-------------------|------------------------------|
| POST   | `/auth/register`  | Register new user            |
| POST   | `/auth/login`     | Login and get JWT token      |

#### Documents

| Method | Endpoint            | Description                  |
|--------|---------------------|------------------------------|
| POST   | `/docs/upload`      | Upload and process document  |
| GET    | `/documents/`       | Get all user documents       |
| GET    | `/documents/{id}`   | Get specific document        |
| DELETE | `/documents/{id}`   | Delete document              |

#### Chat

| Method | Endpoint | Description                     |
|--------|----------|---------------------------------|
| POST   | `/chat/` | Ask question with document IDs  |

## 🔐 Authentication Flow

1. User registers with username, email, and password
2. Password is hashed using Argon2
3. User logs in and receives JWT token
4. Token must be included in subsequent requests:

```http
Authorization: Bearer <token>
```

## 💬 Chat Request Example

**Request:**

```json
POST /chat/
{
    "query": "What models are used in this document?",
    "doc_ids": ["b23ca09a-664d-46f2-a39e-6033c2b67d55"],
    "conversation_id": null
}
```

**Response:**

```json
{
    "answer": "The document uses CNN and ResNet models...",
    "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

## 📊 Database Schema

### Users Table

| Column           | Type     | Description              |
|------------------|----------|--------------------------|
| id               | UUID     | Primary Key              |
| username         | String   | Unique                   |
| email            | String   | Unique                   |
| hashed_password  | String   | Argon2 hashed            |
| is_active        | Boolean  |                          |
| is_superuser     | Boolean  |                          |
| created_at       | DateTime |                          |
| updated_at       | DateTime |                          |

### Documents Table

| Column           | Type     | Description              |
|------------------|----------|--------------------------|
| id               | UUID     | Primary Key              |
| user_id          | UUID     | Foreign Key              |
| file_name        | String   |                          |
| file_type        | String   |                          |
| file_size        | Integer  |                          |
| filebase_key     | String   |                          |
| chunks           | Integer  |                          |
| primary_language | String   |                          |
| created_at       | DateTime |                          |

### Conversations Table

| Column             | Type   | Description              |
|--------------------|--------|--------------------------|
| id                 | UUID   | Primary Key              |
| conversation_uuid  | String | Unique                   |
| user_id            | UUID   | Foreign Key              |
| meta_data          | JSON   |                          |

## 🔍 How RAG Works

1. **Document Upload**:
   - Extract text from PDF/DOCX
   - Split into chunks
   - Generate embeddings via Google Gemini
   - Store embeddings and metadata in Pinecone

2. **Question Answering**:
   - User sends query with document IDs
   - Query is embedded using Google Gemini
   - Vector search retrieves 30 most similar chunks
   - BM25 reranks to top 10 most relevant
   - Mistral AI generates answer from chunks
   - Response returned to user

## 🛡️ Security Features

- **JWT Authentication**: Secure token-based auth
- **Password Hashing**: Argon2 for secure password storage
- **PII Detection**: Redacts/masks sensitive information
- **Rate Limiting**: Prevents abuse of LLM and tools
- **User Isolation**: Separate Pinecone namespaces per user

## 📈 Performance Optimization

- **Batch Processing**: Embeddings processed in batches of 15
- **Connection Pooling**: Database connection pool size: 20
- **Caching**: Conversation memory via LangGraph checkpoint
- **Retry Logic**: Exponential backoff for failed requests

---
