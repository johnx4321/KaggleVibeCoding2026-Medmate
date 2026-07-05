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
from dotenv import load_dotenv

from medmate.memory.store import MemoryStore
from app.orchestrator_demo import DemoOrchestrator

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="MedMate", description="Personal Medication & Care Assistant")

# Determine mode
MEDMATE_MODE = os.getenv("MEDMATE_MODE", "demo").lower()
logger.info(f"Starting MedMate in {MEDMATE_MODE.upper()} mode")

# Always initialize demo_orchestrator as fallback
demo_orchestrator = DemoOrchestrator()

# Initialize ADK agent + runner for LIVE mode if requested
ADK_APP_NAME = "medmate"
ADK_USER_ID = "demo_user"
adk_runner = None
adk_session_service = None
adk_session_id = None
if MEDMATE_MODE == "live":
    try:
        from google.adk import Runner
        from google.adk.sessions import InMemorySessionService
        from medmate.agent import get_root_agent

        adk_agent = get_root_agent()
        adk_session_service = InMemorySessionService()
        adk_runner = Runner(
            agent=adk_agent,
            app_name=ADK_APP_NAME,
            session_service=adk_session_service,
        )
        session = adk_session_service.create_session_sync(
            app_name=ADK_APP_NAME, user_id=ADK_USER_ID
        )
        adk_session_id = session.id
        logger.info(f"✅ ADK agent + runner initialized for LIVE mode (session={adk_session_id})")
    except Exception as e:
        logger.error(f"Failed to initialize ADK agent: {e}", exc_info=True)
        logger.warning("Will fall back to DEMO mode for requests")


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

    response_mode = MEDMATE_MODE
    try:
        if MEDMATE_MODE == "live" and adk_runner:
            try:
                from google.genai import types

                new_message = types.Content(role="user", parts=[types.Part(text=user_input)])
                events = adk_runner.run(
                    user_id=ADK_USER_ID,
                    session_id=adk_session_id,
                    new_message=new_message,
                )

                text_parts = []
                event_error = None
                for event in events:
                    if getattr(event, "error_code", None):
                        event_error = f"{event.error_code}: {getattr(event, 'error_message', '')}"
                    content = getattr(event, "content", None)
                    if content and getattr(content, "parts", None):
                        for part in content.parts:
                            if getattr(part, "text", None):
                                text_parts.append(part.text)

                if text_parts:
                    response = "\n".join(text_parts)
                    logger.info(f"✅ ADK agent response: {response[:100]}...")
                else:
                    # ADK's async Runner swallows model-call exceptions inside
                    # its background thread rather than raising them here, so
                    # an empty event stream must itself be treated as failure.
                    raise RuntimeError(event_error or "LIVE agent returned no content")

            except Exception as live_error:
                logger.error(f"ADK agent error, falling back to DEMO mode: {live_error}", exc_info=True)
                response = demo_orchestrator.process(user_input)
                response_mode = f"demo (live call failed: {live_error})"
        else:
            response = demo_orchestrator.process(user_input)

        return ChatResponse(response=response, mode=response_mode)

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
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
