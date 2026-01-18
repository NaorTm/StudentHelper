# backend/app/api/chat.py
from __future__ import annotations

from fastapi import APIRouter

from app.db import get_conn
from app.schemas import AnswerOut, ConversationMessagesOut, ConversationOut, FeedbackCreateRequest, MessageCreateRequest
from app.config import settings
from app.services.answerer import generate_answer, has_min_relevance
from app.services.reranker import rerank_chunks
from app.services.retrieval import retrieve_chunks

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/conversations", response_model=ConversationOut)
def create_conversation():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO conversations DEFAULT VALUES RETURNING id")
            conversation_id = cur.fetchone()["id"]
        conn.commit()
    return {"id": conversation_id}


@router.post("/conversations/{conversation_id}/messages", response_model=AnswerOut)
def create_message(conversation_id: str, request: MessageCreateRequest):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s) RETURNING id",
                (conversation_id, "user", request.content),
            )
            user_message_id = cur.fetchone()["id"]
        conn.commit()

    chunks = retrieve_chunks(
        query=request.content,
        top_k=request.top_k,
        institution=request.institution,
        language=request.language,
        categories=request.categories,
        effective_date_start=request.effective_date_start,
        effective_date_end=request.effective_date_end,
        active_only=True,
    )

    if settings.reranker_model:
        chunks = rerank_chunks(request.content, chunks, settings.reranker_top_n)

    if not has_min_relevance(chunks):
        answer = {
            "answer_text": "I could not find this in the corpus.",
            "steps": None,
            "citations": [],
            "confidence": "abstain",
            "follow_up_questions": ["Is there a specific policy or institution you want me to check?"],
        }
    else:
        answer = generate_answer(chunks)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s) RETURNING id",
                (conversation_id, "assistant", answer["answer_text"]),
            )
            assistant_message_id = cur.fetchone()["id"]

            cur.execute(
                """
                INSERT INTO retrieval_traces (
                    conversation_id, message_id, retrieved_chunk_ids, similarity_scores,
                    rerank_scores, filters, corpus_snapshot_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    conversation_id,
                    assistant_message_id,
                    [chunk["chunk_id"] for chunk in chunks],
                    [chunk["score"] for chunk in chunks],
                    [chunk.get("rerank_score") for chunk in chunks] if settings.reranker_model else None,
                    {
                        "institution": request.institution,
                        "language": request.language,
                        "categories": request.categories,
                        "effective_date_start": request.effective_date_start.isoformat() if request.effective_date_start else None,
                        "effective_date_end": request.effective_date_end.isoformat() if request.effective_date_end else None,
                    },
                    None,
                ),
            )
        conn.commit()

    return answer


@router.get("/conversations/{conversation_id}", response_model=ConversationMessagesOut)
def get_conversation(conversation_id: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, role, content, created_at FROM messages WHERE conversation_id = %s ORDER BY created_at",
                (conversation_id,),
            )
            messages = cur.fetchall()
    return {"conversation_id": conversation_id, "messages": messages}


@router.post("/feedback")
def create_feedback(request: FeedbackCreateRequest):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO feedback (conversation_id, message_id, rating, flags, notes)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    str(request.conversation_id),
                    str(request.message_id),
                    request.rating,
                    request.flags,
                    request.notes,
                ),
            )
        conn.commit()
    return {"status": "ok"}
