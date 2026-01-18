# AGENTS.md, authoritative implementation spec for Student Rights Copilot

This file is the primary product and engineering specification for this repository. Implementations must follow it. The system is a document grounded assistant for student rights and benefits questions, with strict citation requirements.

## 1) Safety and trust constraints, mandatory

1) The system provides information extracted from the uploaded corpus only. It is not legal advice.  
2) The system must not claim anything that is not supported by retrieved sources.  
3) Every factual claim must include at least one citation.  
4) If no supporting evidence exists, the system must abstain and say it cannot find this in the corpus.  
5) If sources conflict or the clause is ambiguous, the system must mark uncertainty, present both citations, and recommend the official institutional office for clarification.  
6) The answering pipeline must not use external web browsing.  
7) The system must not request or store personal identifiers by default. If the user shares personal data, store only if explicitly needed for the conversation flow, and prefer not storing.

## 2) Product scope

### 2.1 Must have, MVP
1) Admin can upload PDF documents and assign metadata.  
2) System parses PDFs with page anchors, chunks into retrievable units.  
3) System stores embeddings in pgvector and supports similarity search.  
4) Student can ask questions and receive grounded answers with citations.  
5) System logs retrieval traces for audit.  
6) Basic evaluation script runs on a curated question set.

### 2.2 Should have, Phase 2
1) Reranking for improved precision.  
2) Clarifying questions when required parameters are missing.  
3) Admin explain view showing retrieved chunks and scores.  
4) Better section path extraction for numbered clauses.

### 2.3 Could have, Phase 3
1) Eligibility rules engine for common policies, deterministic outcomes with citations.  
2) Study guide generator that compiles a topic summary with citations.

## 3) System architecture, required modules

### 3.1 Backend, FastAPI
Responsibilities:
• Auth, admin token or role based auth  
• Document upload and versioning  
• Chat endpoint, retrieval, answering, citations  
• Evaluation endpoints  
• Retrieval traces and feedback storage

### 3.2 Worker, Celery
Responsibilities:
• Ingestion pipeline tasks  
• Parsing, chunking, embedding  
• Re index jobs  
• Optional evaluation runs

### 3.3 Database, Postgres with pgvector
Store:
• documents, document_versions  
• chunks, embeddings  
• ingestion_jobs  
• conversations, messages  
• retrieval_traces  
• feedback  
• optional eligibility_rules

## 4) API contracts, required endpoints

### 4.1 Health
GET /health  
Returns status and version.

### 4.2 Admin, documents
POST /admin/documents  
POST /admin/documents/{document_id}/versions  
GET /admin/documents  
GET /admin/documents/{document_id}  
POST /admin/document-versions/{version_id}/activate  
GET /admin/ingestion-jobs/{job_id}

Admin endpoints must require ADMIN_TOKEN or equivalent auth.

### 4.3 Search and retrieval transparency
POST /search  
Returns chunks with excerpts and anchors for a given query and filters.

### 4.4 Chat
POST /chat/conversations  
POST /chat/conversations/{conversation_id}/messages  
GET /chat/conversations/{conversation_id}  
POST /chat/feedback

Response from message creation must include:
• answer_text  
• citations list  
• confidence label (supported, uncertain, abstain)  
• follow_up_questions list, optional

## 5) Ingestion pipeline, required behavior

### 5.1 Parsing, PDF
Use a page aligned parser. Each chunk must record:
• page_start, page_end  
• excerpt location, stable enough to audit  
• section_path when possible

Parser must produce deterministic output for the same input file and version.

### 5.2 Chunking strategy
Preferred:
1) Detect headings and numbered clauses.  
2) Chunk by clause boundaries.  
3) Enforce max length and overlap.

Fallback:
1) Token length based chunking with overlap.

Target:
• 300 to 900 tokens per chunk  
• overlap 60 to 120 tokens

### 5.3 Embeddings
Batch embedding requests. Store:
• vector  
• model_name  
• embedding_dim

### 5.4 Indexing
Create an HNSW index in pgvector. Provide migration scripts to update index if embedding model changes.

## 6) Retrieval pipeline, required behavior

1) Embed query, retrieve Top K chunks.  
2) Apply filters:
   • active versions only, default  
   • institution, language, category, date range as provided  
3) Optional reranker reduces to Top N.  
4) Return selected chunks to answerer.

The system must store a retrieval trace for every answer:
• retrieved chunk ids  
• similarity scores  
• rerank scores  
• filters applied  
• corpus snapshot identifier (for audit)

## 7) Answer generation, strict grounding and validation

### 7.1 Output first as structured JSON
The answerer must generate a JSON object with:
• claims: array of claim objects  
• each claim has text and citation_ids  
• steps: optional array  
• confidence label

### 7.2 Validation
Backend must validate:
1) Every claim has at least one citation id.  
2) Every citation id exists in the selected chunk set.  
3) If validation fails, return abstain with explanation and sources.

### 7.3 Rendering
Render final answer as:
1) Summary paragraph  
2) Conditions and exceptions  
3) Steps to act  
4) Sources list with excerpt snippets

### 7.4 Legal advice guard
If the user asks for legal advice:
• respond with informational framing  
• emphasize documents only  
• recommend official institutional office for final interpretation

## 8) Evaluation harness, required

Create scripts in `scripts/`:
• build_eval_set.py, format validation for evaluation JSON  
• run_eval.py, run questions through the chat endpoint with fixed config  
Outputs:
• JSON report  
• HTML report with citations and failure highlighting

Metrics required:
• citation precision, manual or assisted labels  
• answer correctness, label set  
• abstention accuracy  
• latency p50 and p95

## 9) Engineering standards

1) Python style: type hints, clear module boundaries, pydantic schemas.  
2) Testing:
   • unit tests for parsing, chunking, citations formatting  
   • integration test for ingestion job and chat response  
3) Logging: structured logs, include request ids.  
4) Configuration: environment variables with validation.  
5) Security:
   • validate upload file types  
   • limit file size  
   • sanitize filenames  
   • rate limit chat endpoint in production

## 10) Definition of done, MVP

MVP is complete when:
1) Admin can upload a PDF, ingestion completes, chunks are searchable.  
2) Student asks a question, system returns an answer with citations.  
3) A question outside coverage triggers abstention.  
4) Retrieval trace is stored and visible in logs or admin view.  
5) Evaluation set runs and produces a report.

Do not merge changes that reduce grounding quality or citation correctness.
