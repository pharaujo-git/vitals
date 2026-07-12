from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.security import user_from_token
from app.db.session import SessionLocal
from app.repositories.messages import MessageRepository
from app.services.events import change_stream

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/messages")
def message_events(token: str):
    # Authenticate with a short-lived session; never hold one open for the stream.
    with SessionLocal() as db:
        user = user_from_token(db, token)
        user_id = user.id

    def fingerprint() -> str:
        with SessionLocal() as db:
            return MessageRepository(db).fingerprint(user_id)

    return StreamingResponse(
        change_stream(fingerprint),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/{channel}")
def unknown_channel(channel: str):
    raise HTTPException(404, f"Unknown event channel: {channel}")
