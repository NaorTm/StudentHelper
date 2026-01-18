# docs/architecture.md

# Architecture specification, Student Rights Copilot

## 1) High level architecture

### 1.1 Components
1) Frontend web app  
   • Student chat UI  
   • Admin upload UI  
   • Source viewer for cited pages

2) Backend API, FastAPI  
   • Auth and roles  
   • Document management  
   • Chat, retrieval, answer generation  
   • Evaluation endpoints

3) Worker, Celery  
   • Ingestion pipeline tasks  
   • Re indexing  
   • Optional evaluation runs

4) Database, Postgres  
   • Relational tables for documents, versions, chunks, feedback  
   • pgvector for embeddings

5) Cache and broker, Redis  
   • Celery broker and results  
   • Optional caching for hot queries

6) File storage  
   • Local volume for dev  
   • Optional S3 compatible object storage for production

### 1.2 Data flow, ingestion
1) Admin uploads file and metadata to Backend.  
2) Backend stores file and creates a document version record.  
3) Backend enqueues ingestion job to Worker.  
4) Worker parses PDF into page aligned text.  
5) Worker runs chunking, producing chunks with page anchors.  
6) Worker computes embeddings per chunk and stores in pgvector.  
7) Worker updates status, ready for retrieval.

### 1.3 Data flow, query
1) Student sends message to Backend.  
2) Backend optionally classifies intent and extracts missing parameters.  
3) Backend embeds query and retrieves Top K chunks.  
4) Backend optionally reranks candidates.  
5) Backend generates answer from selected chunks only.  
6) Backend returns answer and citations, logs retrieval trace.

---

## 2) Trust and grounding strategy

### 2.1 Strict grounding contract
The answerer must use only retrieved chunks as evidence. It must not introduce unsupported statements.

Implementation pattern:
1) Retrieve sources.  
2) Produce a structured draft where every claim references source ids.  
3) Validate claim to citation mapping.  
4) Render final answer with citations.

### 2.2 Abstention thresholds
Define thresholds to avoid confident hallucinations:
• Minimum similarity score required for answering  
• Minimum number of supporting chunks for complex answers  
• If below thresholds, return abstain with suggested next step

### 2.3 Contradiction handling
If multiple active sources contradict:
1) Mark confidence as uncertain.  
2) Present both citations.  
3) Explain conflict and recommend official channel.

---

## 3) Storage design

### 3.1 Tables
• documents  
• document_versions  
• chunks  
• embeddings  
• ingestion_jobs  
• conversations  
• messages  
• retrieval_traces  
• feedback  
• optional eligibility_rules

### 3.2 Vector indexing
Use pgvector with an HNSW index for scalable similarity search. Store model name and embedding dimension to support migrations.

---

## 4) Ingestion pipeline design

### 4.1 Parsing
Preferred library: PyMuPDF for page aligned extraction.

Responsibilities:
• Extract per page text  
• Capture basic layout cues (titles, headings, clause numbers)  
• Normalize whitespace and bullet markers

### 4.2 Chunking
Two pass approach:
1) Structure pass, detect headings and numbered clauses.  
2) Size pass, enforce max length with overlap.

Chunk metadata:
• page_start, page_end  
• section_path, if available  
• chunk_index  
• source hash for reproducibility

### 4.3 Embeddings
Embed each chunk. Store vectors in pgvector. Use batching and retry with exponential backoff.

---

## 5) Retrieval design

### 5.1 Filtering
Default filters:
• active versions only  
• institution if selected  
• language preference if provided

### 5.2 Reranking
Optional reranker improves precision. It can run as:
• local cross encoder model  
• remote LLM based rerank with strict prompt

Rerank inputs:
• query  
• candidate chunk text  
Rerank outputs:
• rerank_score per chunk

---

## 6) Answer generation design

### 6.1 Prompting strategy
Use a system instruction that enforces:
• answer only from sources  
• every claim needs citations  
• abstain when unsupported  
• avoid legal advice framing

### 6.2 Output validation
Require the model to output JSON:
• list of claims  
• each claim has citation_ids  
• final answer assembled from claims

Validate:
• every claim has at least one citation id  
• cited excerpts contain relevant supporting text  
• if validation fails, fallback to abstain

### 6.3 Citation rendering
Render citations in a consistent style, for example:
(Policy name, version label, page X, excerpt)

---

## 7) Security and privacy

### 7.1 Auth and roles
• Admin role for uploads and management  
• Student role or anonymous session for chat  
• Rate limiting per IP for public deployments

### 7.2 Data minimization
• Do not store personal identifiers by default  
• If optional structured context is stored, encrypt at rest where possible

---

## 8) Observability

### 8.1 Logging
• Ingestion job logs, parser errors  
• Retrieval traces, chunk ids, scores, filters  
• Generation metadata, model, prompt version, validation outcomes

### 8.2 Admin explain view
Expose a view that shows:
• retrieved chunks  
• rerank scores  
• citations used  
• abstention reasons

---

## 9) Deployment notes

### 9.1 Development
Use Docker compose for local Postgres, Redis, Backend, Worker, Frontend.

### 9.2 Production
• Use managed Postgres with pgvector  
• Use object storage for documents  
• Use a job queue and worker autoscaling  
• Add monitoring and alerting
