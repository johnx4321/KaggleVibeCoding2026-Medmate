"""FastAPI server for MedMate with DEMO and LIVE modes."""

import os
import json
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

from medmate.memory.store import MemoryStore
from app.orchestrator_demo import DemoOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="MedMate", description="Personal Medication & Care Assistant")

# Determine mode
MEDMATE_MODE = os.getenv("MEDMATE_MODE", "demo").lower()
logger.info(f"Starting MedMate in {MEDMATE_MODE.upper()} mode")

# Initialize orchestrator for DEMO mode
if MEDMATE_MODE == "demo":
    demo_orchestrator = DemoOrchestrator()


class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    mode: str


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "mode": MEDMATE_MODE}


@app.post("/chat")
async def chat(request: ChatMessage) -> ChatResponse:
    """Chat endpoint - routes to DEMO or LIVE mode."""
    user_input = request.message.strip()

    if not user_input:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        if MEDMATE_MODE == "demo":
            response = demo_orchestrator.process(user_input)
        else:
            # LIVE mode would use the actual ADK agent
            response = "LIVE mode not configured. Set GOOGLE_API_KEY and MEDMATE_MODE=live"

        return ChatResponse(response=response, mode=MEDMATE_MODE)

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/profile")
async def get_profile():
    """Get current user profile."""
    store = MemoryStore()
    return store.get_profile()


@app.post("/profile/seed")
async def seed_profile():
    """Seed a demo profile (for testing/video)."""
    store = MemoryStore()
    store.add_medication("lisinopril", "10mg", "once daily", "blood pressure", "ACE inhibitor")
    store.add_medication("ibuprofen", "200mg", "every 6-8 hours", "pain relief", "as needed for aches")
    store.add_allergy("penicillin")
    store.add_condition("hypertension")
    return {"status": "seeded", "profile": store.get_profile()}


# Serve static files (web UI)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Serve the index.html"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "MedMate API running. Static UI not found."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
