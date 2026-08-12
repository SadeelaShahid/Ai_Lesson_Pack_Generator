from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from router import handle_message
from database import init_db, list_lesson_versions, load_lesson_version

init_db()

app = FastAPI(title="AI Lesson Pack Generator")


class ChatRequest(BaseModel):
    session_id: str
    message: str
    level: Optional[str] = "beginner"
    duration_minutes: Optional[int] = 60


class ChatResponse(BaseModel):
    session_id: str
    route: str
    reply: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    result = handle_message(
        session_id=request.session_id,
        message=request.message,
        level=request.level,
        duration_minutes=request.duration_minutes
    )
    return {
        "session_id": request.session_id,
        "route": result["route"],
        "reply": result["reply"]
    }


@app.get("/versions/{session_id}")
def get_versions(session_id: str):
    versions = list_lesson_versions(session_id)
    return {"session_id": session_id, "versions": versions}


@app.get("/versions/detail/{version_id}")
def get_version_detail(version_id: int):
    version = load_lesson_version(version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return version