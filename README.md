<p align="center">
 <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" />
 <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
 <img src="https://img.shields.io/badge/LangGraph-0.2+-FF6F00?style=for-the-badge&logo=chainlink&logoColor=white" />
 <img src="https://img.shields.io/badge/MongoDB-Atlas-47A248?style=for-the-badge&logo=mongodb&logoColor=white" />
 <img src="https://img.shields.io/badge/Groq-LPU_Inference-F55036?style=for-the-badge&logo=lightning&logoColor=white" />
 <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
 <img src="https://img.shields.io/badge/Chrome-Extension_MV3-4285F4?style=for-the-badge&logo=googlechrome&logoColor=white" />
</p>

<h1 align="center"> NeuroGuard — Agentic AI Platform</h1>

<p align="center">
 <strong>A production-grade platform to build, deploy, and manage custom AI agents — with an integrated Chrome extension for real-time web threat detection.</strong>
</p>

<p align="center">
 <em>Built by <a href="https://github.com/sabarishwaran7"><strong>Sabarishwaran</strong></a></em>
</p>

<br/>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#system-architecture">Architecture</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#project-structure">Project Structure</a> •
  <a href="#langgraph-agent-workflow">Agent Workflow</a> •
  <a href="#rag-pipeline">RAG Pipeline</a> •
  <a href="#neuroguard-chrome-extension">Chrome Extension</a> •
  <a href="#api-reference">API Reference</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#deployment">Deployment</a>
</p>

---

## What is NeuroGuard?

NeuroGuard is not just another chatbot wrapper. It is a **full-stack Agentic AI Platform** that combines three powerful systems into one cohesive product:

| System | What It Does |
|--------|-------------|
| ** Agentic AI Platform** | Create, configure, and deploy custom AI agents with per-agent API keys, system prompts, model selection, and optional RAG |
| ** LangGraph Workflow Engine** | Every agent runs through a compiled multi-node state graph — `Planner → RAG Retrieval → Reasoning` — for structured, plan-and-execute intelligence |
| ** NeuroGuard Chrome Extension** | A Manifest V3 browser extension that monitors every URL in real-time using a node-based threat detection pipeline with SerpApi reputation analysis |

> **Why this matters:** This isn't a toy demo. It's architected like a real SaaS product — JWT auth, bcrypt passwords, rate limiting, API key rotation, FAISS vector stores, MongoDB indexes, Docker containers, and a polished frontend with analytics dashboards.

---

## Features

### AI Agent Management
- **Full CRUD** — Create, read, update, delete agents via REST API
- **Per-agent API keys** — Cryptographically strong (`secrets.token_hex`), SHA-256 hashed storage, prefix display, key rotation
- **Model selection** — Llama 3 8B, Llama 3 70B, Qwen QWQ 32B, DeepSeek R1 Distill via Groq LPU inference
- **Configurable system prompts** — Up to 8,000 characters per agent
- **Memory toggle** — Enable/disable conversation memory per agent
- **RAG toggle** — Enable/disable document-grounded retrieval per agent

### RAG (Retrieval-Augmented Generation)
- **PDF upload & ingestion** — Up to 20MB per file
- **Recursive text chunking** — 1,000 char chunks with 150 char overlap
- **Sentence-Transformers embeddings** — `all-MiniLM-L6-v2` (384-dim)
- **FAISS vector store** — Per-agent isolated indexes with incremental ingestion
- **Similarity search** — Top-k retrieval injected into the reasoning node

### Authentication & Security
- **JWT Bearer tokens** — HS256, 7-day expiry, `HTTPBearer` auto-extraction
- **bcrypt password hashing** — 12 rounds of salted hashing
- **Rate limiting** — SlowAPI middleware (120 req/min on chat, 30/min on login, 12/min on register)
- **CORS protection** — Configurable allowed origins via environment variables
- **API key validation** — SHA-256 digest comparison on every external agent call

### Dashboard & Analytics
- **Real-time stats** — Total agents, API calls today, recent chat activity
- **MongoDB aggregation pipelines** — Efficient per-user usage metrics
- **Daily usage tracking** — Automatic upsert-based API call counters

### NeuroGuard Chrome Extension
- **Real-time URL monitoring** — Scans every tab update and tab switch
- **SerpApi reputation check** — Queries Google for scam/phishing/malware reports
- **Automated blocking** — Redirects harmful sites to a custom blocked page
- **Threat history dashboard** — Full browsing history with risk analysis
- **n8n-inspired workflow engine** — Modular, node-based pipeline architecture

### DevOps & Deployment
- **Docker support** — Multi-stage Dockerfiles for both root and backend
- **Procfile** — Heroku/Render-ready with Uvicorn worker binding
- **Gunicorn + Uvicorn workers** — Production-grade ASGI serving
- **MongoDB Atlas** — Cloud-native database with indexed collections

---

## System Architecture

```mermaid
graph TB
 subgraph Client Layer
 FE[" Frontend<br/>(HTML/CSS/JS)"]
 CE[" Chrome Extension<br/>(Manifest V3)"]
 EXT[" External APIs<br/>(Any HTTP Client)"]
 end

 subgraph API Gateway
 FAST[" FastAPI Server<br/>(Uvicorn + Gunicorn)"]
 CORS[" CORS Middleware"]
 RATE[" Rate Limiter<br/>(SlowAPI)"]
 AUTH[" JWT Auth<br/>(Bearer Token)"]
 end

 subgraph Core Services
 AGENT[" Agent Service<br/>(CRUD + Config)"]
 CHAT[" Chat Service<br/>(LangGraph Invoke)"]
 RAG_SVC[" RAG Service<br/>(PDF → FAISS)"]
 MEM[" Memory Service<br/>(MongoDB Chat History)"]
 USAGE[" Usage Service<br/>(Daily API Counters)"]
 GROQ[" Groq Service<br/>(LLM Inference)"]
 end

 subgraph AI Engine
 LG[" LangGraph<br/>State Machine"]
 PLAN[" Planner Node"]
 RAG_N[" RAG Node"]
 REASON[" Reasoner Node"]
 end

 subgraph Data Layer
 MONGO[(" MongoDB Atlas")]
 FAISS[(" FAISS<br/>Vector Store")]
 FS[(" File System<br/>PDF Uploads")]
 end

 subgraph Extension Engine
 WF[" Workflow Engine"]
 N1[" URL Detection"]
 N2[" SerpApi Check"]
 N3[" Decision Engine"]
 N4[" Block Website"]
 end

 FE -->|REST API| FAST
 CE -->|History API| FAST
 EXT -->|X-API-Key| FAST

 FAST --> CORS --> RATE --> AUTH

 AUTH --> AGENT
 AUTH --> CHAT
 AUTH --> RAG_SVC
 AUTH --> USAGE

 CHAT --> LG
 LG --> PLAN --> RAG_N --> REASON
 PLAN --> GROQ
 RAG_N --> FAISS
 REASON --> GROQ

 CHAT --> MEM
 AGENT --> MONGO
 MEM --> MONGO
 USAGE --> MONGO
 RAG_SVC --> FAISS
 RAG_SVC --> FS

 CE --> WF
 WF --> N1 --> N2 --> N3 --> N4

 style FAST fill:#009688,color:#fff
 style LG fill:#FF6F00,color:#fff
 style MONGO fill:#47A248,color:#fff
 style FAISS fill:#2563eb,color:#fff
 style WF fill:#7c3aed,color:#fff
 style GROQ fill:#F55036,color:#fff
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend Framework** | FastAPI 0.115+ | Async REST API with auto-generated OpenAPI docs |
| **ASGI Server** | Uvicorn + Gunicorn | Production-grade async HTTP serving |
| **LLM Inference** | Groq Cloud (LPU) | Ultra-low-latency inference for Llama 3, Qwen, DeepSeek |
| **Agent Orchestration** | LangGraph 0.2+ | Compiled state-graph workflows with node-based execution |
| **LLM Framework** | LangChain 0.3+ | Model abstraction, document loading, text splitting |
| **Embeddings** | Sentence-Transformers | `all-MiniLM-L6-v2` for 384-dimensional dense vectors |
| **Vector Database** | FAISS (CPU) | Per-agent similarity search indexes |
| **Primary Database** | MongoDB Atlas | Users, agents, chat history, API keys, usage metrics |
| **Auth** | PyJWT + bcrypt | HS256 JWT tokens + 12-round salted password hashing |
| **Rate Limiting** | SlowAPI | IP-based request throttling per endpoint |
| **PDF Processing** | PyPDF | Document loading for RAG ingestion |
| **Frontend** | HTML5 / CSS3 / Vanilla JS | Responsive SPA with Chart.js analytics |
| **Chrome Extension** | Manifest V3 | Service worker-based background threat detection |
| **Containerization** | Docker | Multi-environment reproducible deployments |
| **Deployment** | Render / Heroku / Any PaaS | Procfile + Dockerfile for one-click deploy |

---

## Project Structure

```mermaid
graph LR
 subgraph Root[" NeuroGuard-api-dev"]
 direction TB
 DF[" Dockerfile"]
 REQ[" requirements.txt"]
 GI[" .gitignore"]
 RM[" README.md"]
 end

 subgraph Backend[" backend/"]
 direction TB
 MAIN[" main.py — FastAPI entrypoint"]
 CONF[" config.py — Path & env config"]
 DB[" database.py — MongoDB client"]
 LIM[" limiter_config.py — SlowAPI"]
 FUT[" future_extensions.py — Roadmap"]
 TEST[" test.py — Integration test"]
 PROC[" Procfile — PaaS deploy"]
 BDF[" Dockerfile — Backend container"]

 subgraph Routes[" routes/"]
 AR["agent_routes.py<br/>CRUD + Chat + Dashboard + Public API"]
 AUR["auth_routes.py<br/>Register + Login + Profile"]
 RR["rag_routes.py<br/>PDF Upload & Ingestion"]
 NR["neuroguard_routes.py<br/>Extension History API"]
 end

 subgraph Services[" services/"]
 GS["groq_service.py<br/>LLM model resolution & invocation"]
 LS["langgraph_service.py<br/>Planner → RAG → Reason graph"]
 MS["memory_service.py<br/>Chat history persistence"]
 RS["rag_service.py<br/>PDF → Chunks → FAISS"]
 US["usage_service.py<br/>Daily API call counters"]
 end

 subgraph Models[" models/"]
 SCH["schemas.py<br/>Pydantic request/response models"]
 end

 subgraph Utils[" utils/"]
 SEC["security.py<br/>JWT + bcrypt + auth dependency"]
 AK["api_key.py<br/>Key generation & SHA-256 hashing"]
 end
 end

 subgraph Frontend[" frontend/"]
 direction TB
 IDX[" index.html — Landing page"]
 LOG[" login.html — Auth"]
 REG[" register.html — Signup"]
 DASH[" dashboard.html — Analytics"]
 CA[" create-agent.html — Agent wizard"]
 CH[" chat.html — Chat interface"]
 AG[" agents.html — Agent list"]
 EX[" extension.html — Extension download"]
 BD[" browse-dashboard.html — Browse agents"]

 subgraph Static[" static/"]
 CSS[" css/ — Stylesheets"]
 JSF[" js/ — Client scripts"]
 end
 end

 subgraph Extension[" chrome-extension/"]
 direction TB
 MAN[" manifest.json — MV3 config"]
 BG[" background.js — Service worker"]
 WFE[" workflow.js — Pipeline engine"]
 CFG[" config.js — API keys & keywords"]
 POP[" popup.html/js — Status popup"]
 BLK[" blocked.html/js — Block page"]
 HIS[" history.html/js — Scan history"]
 ICO[" icons/ — Extension icons"]
 end

 Root --> Backend
 Root --> Frontend
 Root --> Extension
```

---

## LangGraph Agent Workflow

Every chat message — whether from the frontend or an external API call — is processed through a **compiled LangGraph state machine**. This ensures structured, multi-step reasoning instead of raw single-shot LLM calls.

```mermaid
flowchart TD
    START(["User Message"]) --> PLAN

    subgraph PLAN_BLOCK ["STAGE 1 — Planner"]
        PLAN["Generate Action Plan"]
        PLAN_DESC["Receives user query<br/>Calls Groq LLM with planning prompt<br/>Outputs max 5 bullet plan<br/>Does NOT answer the user yet"]
    end

    PLAN --> CHECK

    subgraph RAG_BLOCK ["STAGE 2 — RAG Retrieval"]
        CHECK{"RAG Enabled?"}
        CHECK -->|Yes| LOAD["Load FAISS Index"]
        LOAD --> SEARCH["Top-K Similarity Search"]
        SEARCH --> INJECT["Inject Retrieved Context"]
        CHECK -->|No| SKIP["Skip - empty context"]
    end

    INJECT --> BUILD
    SKIP --> BUILD

    subgraph REASON_BLOCK ["STAGE 3 — Reasoner"]
        BUILD["Build Augmented System Prompt"]
        BUILD_DESC["Combines:<br/>- Original system prompt<br/>- Internal plan hidden from user<br/>- RAG context if enabled<br/>- Conversation memory if enabled"]
        BUILD --> INVOKE["Invoke Groq LLM"]
        INVOKE --> EXTRACT["Extract and Return Response"]
    end

    EXTRACT --> DONE(["Final Response"])

    style PLAN fill:#2563eb,color:#fff
    style CHECK fill:#7c3aed,color:#fff
    style BUILD fill:#059669,color:#fff
    style INVOKE fill:#F55036,color:#fff
    style DONE fill:#0f172a,color:#fff
    style PLAN_DESC fill:#f1f5f9,color:#334155,stroke:none
    style BUILD_DESC fill:#f1f5f9,color:#334155,stroke:none
```

### Supported Models

| Model ID | Backbone | Parameters | Use Case |
|----------|----------|------------|----------|
| `llama3-8b-8192` | Llama 3 | 8B | Fast general-purpose tasks |
| `llama3-70b-8192` | Llama 3 | 70B | Complex reasoning & analysis |
| `qwen-qwq-32b` | Qwen | 32B | Multilingual & code generation |
| `deepseek-r1-distill` | DeepSeek R1 | 70B (distilled) | Advanced chain-of-thought reasoning |

---

## RAG Pipeline

The RAG system provides **per-agent document grounding** using a production-ready ingestion and retrieval pipeline.

```mermaid
flowchart LR
 subgraph Ingestion[" Document Ingestion"]
 PDF[" PDF Upload<br/>(max 20MB)"]
 LOAD[" PyPDFLoader"]
 SPLIT[" RecursiveCharacterTextSplitter<br/>(1000 chars / 150 overlap)"]
 EMBED[" HuggingFace Embeddings<br/>(all-MiniLM-L6-v2)"]
 STORE[" FAISS Index<br/>(per-agent isolation)"]
 end

 subgraph Retrieval[" Query-Time Retrieval"]
 QUERY[" User Query"]
 QEMBED[" Embed Query"]
 SEARCH[" Similarity Search<br/>(top-4 chunks)"]
 CONTEXT[" Retrieved Context"]
 end

 PDF --> LOAD --> SPLIT --> EMBED --> STORE
 QUERY --> QEMBED --> SEARCH --> CONTEXT
 STORE -.->|"Index"| SEARCH

 style STORE fill:#2563eb,color:#fff
 style EMBED fill:#7c3aed,color:#fff
```

### Key Design Decisions:
- **Per-agent isolation** — Each agent has its own FAISS index directory (`vectorstore/<agent_id>/`)
- **Incremental ingestion** — New PDFs are merged into existing indexes, not overwritten
- **Chunk metadata** — Source page numbers preserved through LangChain document objects
- **20MB upload limit** — Server-side validation before disk write

---

## NeuroGuard Chrome Extension

The extension implements a **custom n8n-inspired workflow engine** — a lightweight, node-based automation system where each node receives context, executes logic, and passes results to the next node.

```mermaid
flowchart TD
 START((" Tab Event<br/>(Updated / Switched)")) --> N1

 subgraph Pipeline[" Threat Detection Pipeline v1.0"]
 N1[" Node 1: URL Detection<br/>Validate URL • Extract domain<br/>Skip chrome:// and extension pages"]
 N2[" Node 2: SerpApi Check<br/>Query Google for:<br/>• domain + scam<br/>• domain + phishing<br/>• domain + malware<br/>Match against 11 threat keywords"]
 N3[" Node 3: Decision Engine<br/>Evaluate reputation signals<br/>+ AMTSO/EICAR simulation detection<br/>→ ALLOW or BLOCK"]
 N4[" Node 4: Block Website<br/>Store explanation in chrome.storage<br/>Redirect tab to blocked.html"]
 end

 N1 -->|"context"| N2
 N2 -->|"context"| N3
 N3 -->|"context"| N4

 N1 -.->|"_abort"| SKIP[" Skip Pipeline"]
 N4 -->|"ALLOWED"| SAFE[" Safe - No Action"]
 N4 -->|"BLOCKED"| BLOCK[" Blocked Page"]

 N4 --> HIST[" Save to History"]

 style N1 fill:#2563eb,color:#fff
 style N2 fill:#7c3aed,color:#fff
 style N3 fill:#F59E0B,color:#000
 style N4 fill:#EF4444,color:#fff
 style BLOCK fill:#991B1B,color:#fff
 style SAFE fill:#059669,color:#fff
```

### Workflow Engine Architecture

```mermaid
classDiagram
 class WorkflowEngine {
 -workflow: WorkflowDefinition
 -executionLog: Array
 +run(initialContext): Promise~Context~
 }

 class WorkflowDefinition {
 +id: string
 +name: string
 +version: string
 +nodes: string[]
 }

 class NodeRegistry {
 +registerNode(id, config)
 +NODE_REGISTRY: Map
 }

 class Node {
 +id: string
 +label: string
 +description: string
 +execute(context): Object
 }

 WorkflowEngine --> WorkflowDefinition
 WorkflowEngine --> NodeRegistry
 NodeRegistry --> Node

 class Context {
 +url: string
 +tabId: number
 +domain: string
 +serpRisky: boolean
 +decision: string
 +_abort: boolean
 +_executionLog: Array
 }

 WorkflowEngine --> Context
```

---

## API Reference

### Authentication

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| `POST` | `/api/auth/register` | Register new user | 12/min |
| `POST` | `/api/auth/login` | Login & get JWT token | 30/min |
| `GET` | `/api/auth/me` | Get current user profile | — |

### Agent Management

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/agents` | Create a new agent | Bearer JWT |
| `GET` | `/api/agents` | List all user's agents | Bearer JWT |
| `GET` | `/api/agents/{id}` | Get agent details | Bearer JWT |
| `PATCH` | `/api/agents/{id}` | Update agent config | Bearer JWT |
| `DELETE` | `/api/agents/{id}` | Delete agent & all data | Bearer JWT |
| `POST` | `/api/agents/{id}/regenerate-key` | Rotate API key | Bearer JWT |

### Chat & AI

| Method | Endpoint | Description | Auth | Rate Limit |
|--------|----------|-------------|------|------------|
| `POST` | `/api/chat` | Chat with your agent | Bearer JWT | 120/min |
| `POST` | `/agent/{name}` | Public agent invocation | X-API-Key | 120/min |

### RAG Document Upload

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/agents/{id}/rag/upload` | Upload PDF for RAG | Bearer JWT |

### Dashboard

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/dashboard/stats` | Get dashboard metrics | Bearer JWT |

### NeuroGuard Extension

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/neuroguard/history` | Add browsing history entry |
| `GET` | `/api/neuroguard/history` | Get all history entries |
| `DELETE` | `/api/neuroguard/history` | Clear all history |
| `GET` | `/api/neuroguard/stats` | Get aggregated threat stats |
| `GET` | `/api/extension/download` | Download extension as ZIP |

### Usage Example — External Agent API

```bash
curl -X POST https://your-api.com/agent/resume_builder \
 -H "X-API-Key: Aiml_agent_72a6a8a722760b271e386586..." \
 -H "Content-Type: application/json" \
 -d '{"message": "Build a resume for a senior ML engineer"}'
```

**Response:**
```json
{
 "reply": "Here's a professional resume for a Senior ML Engineer...",
 "agent_name": "resume_builder",
 "used_rag": false,
 "used_memory": true
}
```

---

## Database Schema

```mermaid
erDiagram
 USERS {
 ObjectId _id PK
 string email UK
 string password
 string full_name
 datetime created_at
 }

 AGENTS {
 ObjectId _id PK
 string user_id FK
 string name
 string model_name
 string system_prompt
 bool memory_enabled
 bool rag_enabled
 datetime created_at
 datetime updated_at
 }

 API_KEYS {
 ObjectId _id PK
 string agent_id FK
 string user_id FK
 string key_sha256 UK
 string key_prefix
 datetime created_at
 }

 CHAT_HISTORY {
 ObjectId _id PK
 string user_id FK
 string agent_id FK
 string role
 string content
 datetime created_at
 }

 UPLOADED_FILES {
 ObjectId _id PK
 string user_id FK
 string agent_id FK
 string filename
 string stored_path
 int chunks
 datetime created_at
 }

 API_USAGE {
 ObjectId _id PK
 string user_id FK
 string day UK
 int count
 }

 USERS ||--o{ AGENTS : "owns"
 AGENTS ||--o| API_KEYS : "has"
 USERS ||--o{ CHAT_HISTORY : "participates"
 AGENTS ||--o{ CHAT_HISTORY : "receives"
 AGENTS ||--o{ UPLOADED_FILES : "stores"
 USERS ||--o{ API_USAGE : "tracked"
```

---

## Getting Started

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Backend runtime |
| MongoDB | 6.0+ or Atlas | Primary database |
| Groq API Key | — | LLM inference |
| SerpApi Key | — | Chrome extension (optional) |

### 1. Clone the Repository

```bash
git clone https://github.com/sabarishwaran7/Neuroguard-api-dev.git
cd Neuroguard-api-dev
```

### 2. Set Up Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# 
# NeuroGuard — Environment Configuration
# 

# MongoDB
MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/?retryWrites=true
MONGO_DB=agentic_platform

# Authentication
JWT_SECRET=your-super-secret-jwt-key-change-this

# Groq LLM
GROQ_API_KEY=gsk_your_groq_api_key_here

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# Optional overrides
# UPLOADS_DIR=/custom/path/to/uploads
# VECTORSTORE_DIR=/custom/path/to/vectorstore
# FRONTEND_DIR=/custom/path/to/frontend
# HF_EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Run the Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The application will be live at **`http://localhost:8000`** with:
- Landing page at `/`
- Dashboard at `/dashboard`
- Chat at `/chat`
- API docs at `/docs` (auto-generated by FastAPI)

### 5. Install Chrome Extension (Optional)

1. Navigate to `chrome://extensions/`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select the `chrome-extension/` directory
5. Add your SerpApi key in `config.js`

---

## Deployment

### Docker

```bash
# From project root
docker build -t neuroguard .
docker run -p 10000:10000 --env-file backend/.env neuroguard
```

### Backend-only Docker

```bash
cd backend
docker build -t neuroguard-backend .
docker run -p 8000:8000 --env-file .env neuroguard-backend
```

### Render / Heroku

The project includes a `Procfile` for instant PaaS deployment:

```
web: uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Simply connect your Git repo and set the environment variables in the platform dashboard.

---

## Roadmap

The platform is designed with extensibility in mind. Reserved extension points are already defined in the codebase:

| Feature | Status | Description |
|---------|--------|-------------|
| Multi-Agent Orchestration | Planned | Supervisor graphs, agent handoffs |
| Voice Agents | Planned | Streaming STT/TTS, telephony bridges |
| Vision Agents | Planned | Image/video tools, multimodal messages |
| Browser Agents | Planned | Headless automation, policy sandboxes |
| Agent Marketplace | Planned | Templates, versioning, publishing |
| Team Collaboration | Planned | Workspaces, RBAC, audit trails |

---

## Testing

Run the included integration test to verify your setup:

```bash
cd backend
python test.py
```

This sends a test message to a running agent and prints the response.

---

## Security Model

```mermaid
flowchart TD
 REQ[" Incoming Request"] --> TYPE{Request Type?}

 TYPE -->|"Frontend User"| JWT[" JWT Bearer Token"]
 TYPE -->|"External API"| APIKEY[" X-API-Key Header"]

 JWT --> DECODE["Decode HS256 Token"]
 DECODE --> EXPIRY{"Expired?"}
 EXPIRY -->|Yes| REJECT_1[" 401 Token Expired"]
 EXPIRY -->|No| EXTRACT["Extract user_id from 'sub'"]
 EXTRACT --> AUTHORIZE[" Authorized"]

 APIKEY --> HASH["SHA-256 Hash Key"]
 HASH --> LOOKUP["Query api_keys collection"]
 LOOKUP --> FOUND{"Key Found?"}
 FOUND -->|No| REJECT_2[" 401 Invalid API Key"]
 FOUND -->|Yes| MATCH["Match agent_name in URL"]
 MATCH --> AUTHORIZE

 AUTHORIZE --> RATE{"Rate Limit OK?"}
 RATE -->|No| REJECT_3[" 429 Too Many Requests"]
 RATE -->|Yes| PROCESS[" Process Request"]

 style AUTHORIZE fill:#059669,color:#fff
 style REJECT_1 fill:#991B1B,color:#fff
 style REJECT_2 fill:#991B1B,color:#fff
 style REJECT_3 fill:#B45309,color:#fff
```

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is open source and available under the [MIT License](LICENSE).

---

<p align="center">
  <strong>Built by <a href="https://github.com/sabarishwaran7">Sabarishwaran</a></strong>
  <br/>
  <sub>If this project helped you, consider giving it a star</sub>
</p>
