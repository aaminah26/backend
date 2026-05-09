import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import Base, engine
from routers import auth, students

import models.user
import models.student

# Load .env variables
load_dotenv()
from routers import auth, students, ai
FRONTEND_URL=os.getenv("FRONTEND_URL","http://localhost:5173")

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Student Management API",
    version="1.0.0"
)

# ─────────────────────────────────────────────
# CORS FIX (IMPORTANT PART)
# ─────────────────────────────────────────────
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://127.0.0.1:5173",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# ROUTERS
# ─────────────────────────────────────────────
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(students.router, prefix="/students", tags=["Students"])
app.include_router(ai.router)
# ─────────────────────────────────────────────
# TEST ROUTE
# ─────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Student API is running"}