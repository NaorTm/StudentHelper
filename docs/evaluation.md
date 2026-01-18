# docs/evaluation.md

# Evaluation specification

## 1) Goals
Ensure the system produces evidence grounded answers, with correct citations, and abstains when the corpus is insufficient.

## 2) Evaluation dataset
Create an evaluation set with:
• question_id  
• question_text  
• intent_category  
• required_context (optional)  
• ground_truth_citations, list of chunk ids or document plus page anchors  
• ground_truth_answer_summary, short expected outcome  
• notes, edge cases, ambiguity markers

Sources for questions:
• real student questions (anonymized)  
• policy clause based questions  
• adversarial questions that are not covered by the corpus

## 3) Metrics

### 3.1 Citation precision
Definition: fraction of cited excerpts that directly support the associated claim.

Scoring options:
• manual binary label per claim  
• assisted label with human verification

### 3.2 Answer correctness
Definition: whether the answer’s conclusion matches ground truth, given the same corpus.

Labels:
• correct  
• partially correct  
• incorrect  
• unsupported

### 3.3 Abstention accuracy
Definition: abstain when the corpus lacks evidence, answer when evidence exists.

Metrics:
• abstain true positive rate  
• abstain false positive rate

### 3.4 Coverage
Definition: fraction of evaluation questions that can be answered from the corpus with high confidence.

### 3.5 Latency
Track p50 and p95 end to end latency.

## 4) Evaluation procedure
1) Run the evaluation set through the system using a fixed model config.  
2) Log retrieval trace and generated citations.  
3) Produce a JSON report with per question results.  
4) Produce an HTML report highlighting failures and showing citations.

## 5) Regression gates
Block merging changes if:
• citation precision drops below threshold  
• abstain false positive rate increases beyond threshold  
• latency p95 exceeds threshold

## 6) Example report fields
• model_config  
• corpus_snapshot_id  
• overall_metrics  
• per_question_results with:
  • retrieved_chunks  
  • citations_used  
  • confidence  
  • evaluation_labels  
  • notes
