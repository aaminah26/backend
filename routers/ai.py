# routers/ai.py
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from dependencies import get_current_user

router = APIRouter(prefix="/ai", tags=["AI"])

# ── Create the Gemini client once when this module is imported ───────
# These lines run at startup — NOT inside the route function
if not os.getenv("GEMINI_API_KEY"):
    raise RuntimeError("GEMINI_API_KEY is not set in .env")

client = genai.Client()   # reads GEMINI_API_KEY from environment automatically

MODEL_NAME = "gemini-3.1-flash-lite"
GENERATION_CONFIG = types.GenerateContentConfig(
    temperature=0.7,
    max_output_tokens=512,
)

# ── System context — tells Gemini who it is ──────────────────────────
SYSTEM_CONTEXT = """You are a Python and full stack development tutor
for college students who are new to programming.

Response rules:
- Start with a simple real-world analogy before the technical explanation
- Use a short, runnable Python code example when relevant (under 10 lines)
- Keep answers under 200 words unless the question genuinely needs more
- If asked about something outside Python or web development, respond:
  "I am a programming assistant — please ask a Python or web development question."
- Never use jargon without immediately explaining it

The student is learning: Python, FastAPI, React, SQLite, and basic AI.
Their experience level: beginner, first programming course."""
# ── Pydantic schemas ─────────────────────────────────────────────────
class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

class AskResponse(BaseModel):
    answer: str


# ── Protected AI route ────────────────────────────────────────────────
@router.post("/ask", response_model=AskResponse)
def ask_ai(
    request: AskRequest,
    current_user=Depends(get_current_user)   # JWT protection
):
    # Combine system context with the user's question
    full_prompt = f"{SYSTEM_CONTEXT}\n\nStudent question: {request.question}"

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=full_prompt,
            config=GENERATION_CONFIG,
        )
        return AskResponse(answer=response.text)

    except ValueError:
        # Safety filter blocked the response
        raise HTTPException(
            status_code=400,
            detail="This question could not be answered. Please rephrase it."
        )
    except Exception as e:
        print(f"Gemini error: {e}")   # log to server console
        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable. Try again in a moment."
        )