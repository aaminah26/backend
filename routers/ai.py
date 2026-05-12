# routers/ai.py

import os
import json
from typing import Dict, Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from google import genai
from google.genai import types

from dependencies import get_current_user

# ─────────────────────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────────────────────

router = APIRouter(prefix="/ai", tags=["AI"])

# ─────────────────────────────────────────────────────────────
# Environment Check
# ─────────────────────────────────────────────────────────────

if not os.getenv("GEMINI_API_KEY"):
    raise RuntimeError("GEMINI_API_KEY is not set in .env")

# ─────────────────────────────────────────────────────────────
# Gemini Client
# ─────────────────────────────────────────────────────────────

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL_NAME = "gemini-2.5-flash"

GENERATION_CONFIG = types.GenerateContentConfig(
    temperature=0.7,
    max_output_tokens=512,
)

# ─────────────────────────────────────────────────────────────
# System Context
# ─────────────────────────────────────────────────────────────

SYSTEM_CONTEXT = """
You are a helpful programming assistant for college students learning
Python full stack development.

Help with:
- Python
- FastAPI
- React
- SQL / SQLite
- Web development
- AI chatbots
- APIs
- Authentication

Explain concepts clearly using beginner-friendly language and real-world
analogies. Use short code examples when useful.

Keep answers concise and under 200 words unless more detail is required.
"""

# ─────────────────────────────────────────────────────────────
# In-memory Chat Sessions
# ─────────────────────────────────────────────────────────────

chat_sessions: Dict[int, object] = {}

def get_or_create_session(user_id: int):
    if user_id not in chat_sessions:
        chat_sessions[user_id] = client.chats.create(
            model=MODEL_NAME,
            history=[
                {
                    "role": "user",
                    "parts": [{"text": SYSTEM_CONTEXT}]
                },
                {
                    "role": "model",
                    "parts": [{"text": "Understood. Ready to help."}]
                }
            ]
        )

    return chat_sessions[user_id]

# ─────────────────────────────────────────────────────────────
# Pydantic Schemas
# ─────────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

class AskResponse(BaseModel):
    answer: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)

class ChatResponse(BaseModel):
    reply: str


class SummariseRequest(BaseModel):
    text: str = Field(min_length=20, max_length=5000)
    max_words: int = Field(default=150, ge=30, le=500)

class SummariseResponse(BaseModel):
    summary: str


class ExplainRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=300)
    level: Literal["beginner", "intermediate", "expert"] = "beginner"

class ExplainResponse(BaseModel):
    explanation: str


class StreamRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)

# ─────────────────────────────────────────────────────────────
# Explain Levels
# ─────────────────────────────────────────────────────────────

LEVEL_PERSONAS = {
    "beginner": "a school student who has never programmed before",
    "intermediate": "a college student who knows Python basics",
    "expert": "a senior software engineer who wants implementation details",
}

# ─────────────────────────────────────────────────────────────
# Ask Route
# ─────────────────────────────────────────────────────────────

@router.post("/ask", response_model=AskResponse)
def ask_ai(
    request: AskRequest,
    current_user=Depends(get_current_user)
):
    full_prompt = (
        f"{SYSTEM_CONTEXT}\n\n"
        f"Student question: {request.question}"
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=full_prompt,
            config=GENERATION_CONFIG,
        )

        return AskResponse(
            answer=response.text.strip()
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="This question could not be answered. Please rephrase it."
        )

    except Exception as exc:
        print(f"[ask] Gemini error: {exc}")

        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable."
        )

# ─────────────────────────────────────────────────────────────
# Chat Route
# ─────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
def chat_with_ai(
    request: ChatRequest,
    current_user=Depends(get_current_user),
):
    session = get_or_create_session(current_user.id)

    try:
        response = session.send_message(
            request.message
        )

        return ChatResponse(
            reply=response.text.strip()
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Message could not be processed. Try rephrasing."
        )

    except Exception as exc:
        print(f"[chat] Gemini error: {exc}")

        raise HTTPException(
            status_code=503,
            detail="AI service unavailable."
        )

# ─────────────────────────────────────────────────────────────
# Summarize Route
# ─────────────────────────────────────────────────────────────

@router.post("/summarize", response_model=SummariseResponse)
def summarize_text(
    request: SummariseRequest,
    current_user=Depends(get_current_user),
):
    prompt = (
        f"Summarise the following text in no more than "
        f"{request.max_words} words.\n\n"
        f"Return only the summary.\n\n"
        f"TEXT:\n{request.text}"
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=600,
            )
        )

        return SummariseResponse(
            summary=response.text.strip()
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Content could not be processed."
        )

    except Exception as exc:
        print(f"[summarize] Gemini error: {exc}")

        raise HTTPException(
            status_code=503,
            detail="AI service unavailable."
        )

# ─────────────────────────────────────────────────────────────
# Explain Route
# ─────────────────────────────────────────────────────────────

@router.post("/explain", response_model=ExplainResponse)
def explain_topic(
    request: ExplainRequest,
    current_user=Depends(get_current_user),
):
    persona = LEVEL_PERSONAS[request.level]

    prompt = (
        f"Explain the following to {persona}.\n"
        f"Include a real-world analogy.\n"
        f"If relevant, add a short Python code example "
        f"(5 lines max).\n"
        f"Keep the explanation under 200 words.\n\n"
        f"TOPIC: {request.topic}"
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=GENERATION_CONFIG,
        )

        return ExplainResponse(
            explanation=response.text.strip()
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Content could not be processed."
        )

    except Exception as exc:
        print(f"[explain] Gemini error: {exc}")

        raise HTTPException(
            status_code=503,
            detail="AI service unavailable."
        )

# ─────────────────────────────────────────────────────────────
# Streaming Generator (SSE)
# ─────────────────────────────────────────────────────────────

def stream_chat_response(user_id: int, message: str):
    """
    Stream Gemini responses chunk-by-chunk.
    """

    session = get_or_create_session(user_id)

    try:
        for chunk in session.send_message_stream(message):

            if chunk.text:
                data = json.dumps({
                    "chunk": chunk.text
                })

                yield f"data: {data}\n\n"

        yield "data: [DONE]\n\n"

    except ValueError:
        error = json.dumps({
            "error": "Content blocked — try rephrasing."
        })

        yield f"data: {error}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as exc:
        print(f"[stream] Gemini error: {exc}")

        error = json.dumps({
            "error": "AI service temporarily unavailable."
        })

        yield f"data: {error}\n\n"
        yield "data: [DONE]\n\n"

# ─────────────────────────────────────────────────────────────
# Streaming Route
# ─────────────────────────────────────────────────────────────

@router.post("/stream")
def stream_ai_response(
    request: StreamRequest,
    current_user=Depends(get_current_user),
):
    return StreamingResponse(
        stream_chat_response(
            current_user.id,
            request.message
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )

# ─────────────────────────────────────────────────────────────
# Reset Chat Route
# ─────────────────────────────────────────────────────────────

@router.delete("/chat/reset", status_code=204)
def reset_chat(
    current_user=Depends(get_current_user)
):
    chat_sessions.pop(current_user.id, None)

    return Response(status_code=204)