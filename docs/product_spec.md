# docs/product_spec.md

# Product specification, Student Rights Copilot

## 1) Overview

### 1.1 Problem statement
Students, especially reservists, often cannot determine which benefits, accommodations, and procedures apply to them. The relevant information is distributed across institutional policies, FAQs, and official regulations, often with multiple versions and ambiguous phrasing.

### 1.2 Product goal
Provide a “mini Copilot” that answers student rights questions using only an approved document corpus, with precise citations to the exact clause, page, and version that supports each claim.

### 1.3 Success criteria
1) Citation grounded answers, every factual claim is supported by at least one citation.  
2) Abstention correctness, if evidence is missing or ambiguous, the system states this explicitly.  
3) Fast source navigation, users can open the cited page and see the excerpt immediately.  
4) Version awareness, answers prefer currently active versions, older versions remain auditable.  
5) Evaluation quality, a curated test set shows high citation precision and low unsupported output.

### 1.4 Non goals
1) Legal advice, interpretation beyond the documents, or binding guidance.  
2) General internet search during answering, the system uses the uploaded corpus only.  
3) Automated submission of forms or filings, the system can guide but not execute.

---

## 2) Users and roles

### 2.1 Student user
• Asks questions, expects clear steps and citations  
• May provide context, reservist status, dates, course type  
• Needs short answers first, details on demand

### 2.2 Admin curator
• Uploads documents, sets metadata, manages versions  
• Reviews parsing quality  
• Monitors feedback and coverage gaps

### 2.3 Reviewer evaluator
• Creates evaluation questions  
• Validates citation correctness  
• Tracks regressions across model changes

---

## 3) Core workflows

### 3.1 Document ingestion, admin
1) Upload a document file.  
2) Provide metadata, institution, category, language, effective date, published date, tags.  
3) System parses the file into page aligned text.  
4) System chunks the content into section aware chunks.  
5) System computes embeddings and stores them.  
6) System marks the version as active or inactive, based on admin choice.  
7) Admin can preview chunks and confirm anchors.

### 3.2 Question answering, student
1) Student asks a question.  
2) System classifies intent category and detects required parameters.  
3) If key parameters are missing, ask 1 to 3 targeted questions.  
4) Retrieve relevant chunks from active versions first, apply filters.  
5) Optional reranking to improve precision.  
6) Generate an answer grounded only in selected chunks.  
7) Return answer plus citations, plus follow up questions if needed.

### 3.3 Eligibility style queries
For questions implying eligibility, the assistant returns one of:
• Supported eligible, with citations  
• Supported not eligible, with citations  
• Uncertain, explains what is missing or ambiguous, with citations

Phase 1 can be RAG only. Phase 2 can add a small deterministic eligibility rules layer for common cases.

---

## 4) Functional requirements

### 4.1 Document management
1) Support PDF ingestion (required).  
2) Optional ingestion for HTML and DOCX.  
3) Document identity with versioning:
   1) Many versions per document, one or more can be active.  
   2) Deactivate old versions without deletion for audit.  
4) Metadata fields:
   1) institution  
   2) source type (policy, regulation, FAQ, form)  
   3) effective date, published date, revision date  
   4) language  
   5) categories and tags  
   6) trust level (primary official, secondary official summary)

### 4.2 Parsing and anchoring
1) Parse PDFs with page boundaries preserved.  
2) Store page start and page end per chunk.  
3) When feasible, detect headings and section paths, store them.  
4) Store a stable excerpt and its location so citations can be audited later.

### 4.3 Chunking
1) Prefer section aware splitting using headings and numbered clauses.  
2) Fallback to token length splitting with overlap.  
3) Typical chunk target length:
   1) 300 to 900 tokens for retrieval chunks  
   2) Overlap 60 to 120 tokens  
4) Preserve formatting cues, lists, clause numbers.

### 4.4 Embeddings and vector store
1) Compute embeddings for each chunk.  
2) Store vectors in pgvector.  
3) Support filters:
   1) institution  
   2) language  
   3) category and tags  
   4) effective date range  
   5) active version only, default on

### 4.5 Retrieval and reranking
1) Embedding retrieval returns Top K candidates.  
2) Optional reranker reduces to Top N for answering.  
3) Retrieval trace must be logged for audit, including scores and filters applied.

### 4.6 Answer generation
1) The assistant must answer only from provided sources.  
2) Each factual claim must be attached to at least one citation.  
3) If the model cannot support a claim, it must abstain from making it.  
4) The output format must be consistent:
   1) Short summary  
   2) Conditions and exceptions  
   3) Steps to act  
   4) Sources

### 4.7 Citation formatting
A citation must include:
1) document title  
2) version label and dates  
3) page range  
4) optional section path  
5) excerpt snippet  
6) internal chunk id for audit

### 4.8 Abstention policy
1) If no chunk meets a minimum relevance threshold, return “not found in corpus”.  
2) If evidence is contradictory, return “ambiguous”, show both clauses, suggest official contact.  
3) If the user requests legal advice, respond informationally and recommend official channels.

### 4.9 Feedback
1) User rating per answer, helpful or not helpful.  
2) Flags:
   1) wrong citation  
   2) missing coverage  
   3) outdated policy  
   4) unclear answer  
3) Admin dashboard for most frequent queries and low satisfaction clusters.

---

## 5) Non functional requirements

### 5.1 Privacy
1) Default to anonymous sessions.  
2) Avoid collecting personal identifiers.  
3) If structured context is collected (dates, status), store minimally and optionally.

### 5.2 Security
1) Admin endpoints require authentication.  
2) Document uploads are restricted to admins.  
3) Sanitize filenames and validate file types.

### 5.3 Reliability
1) Ingestion jobs must be resumable.  
2) Store job status and errors.  
3) Re index can be triggered for a version or an entire corpus.

### 5.4 Observability
1) Log retrieval traces.  
2) Log answer generation metadata (model, prompt version).  
3) Provide an admin explain view.

---

## 6) Output schemas

### 6.1 Citation object
• citation_id  
• document_title  
• document_version_label  
• effective_date  
• pages (start, end)  
• section_path (optional)  
• excerpt  
• chunk_id  
• relevance_score

### 6.2 Answer object
• answer_text  
• steps (optional list)  
• citations (list)  
• confidence (supported, uncertain, abstain)  
• follow_up_questions (optional list)

---

## 7) Roadmap

### Phase 1, MVP
• PDF ingestion, chunking, embeddings, retrieval  
• Answering grounded with citations  
• Admin upload and activation  
• Basic evaluation script

### Phase 2, precision and UX
• Reranking  
• Better section extraction  
• Clarifying questions for missing parameters  
• Explain view

### Phase 3, eligibility rules
• Rule storage and execution for common policies  
• Outcome labels, eligible, not eligible, uncertain  
• Rule backed citations
