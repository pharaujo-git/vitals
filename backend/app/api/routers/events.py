from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.security import user_from_token
from app.db.session import SessionLocal
from app.repositories.messages import MessageRepository
from app.repositories.notifications import NotificationRepository
from app.services.events import change_stream

router = APIRouter(prefix="/events", tags=["events"])

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


def _stream_for(token: str, repository_class, method_name: str) -> StreamingResponse:
    # Authenticate with a short-lived session; never hold one open for the stream.
    with SessionLocal() as db:
        user = user_from_token(db, token)
        user_id = user.id

    def fingerprint() -> str:
        with SessionLocal() as db:
            return getattr(repository_class(db), method_name)(user_id)

    return StreamingResponse(
        change_stream(fingerprint), media_type="text/event-stream", headers=_SSE_HEADERS
    )


@router.get("/messages")
def message_events(token: str):
    return _stream_for(token, MessageRepository, "fingerprint")


@router.get("/notifications")
def notification_events(token: str):
    return _stream_for(token, NotificationRepository, "fingerprint")


@router.get("/{channel}")
def unknown_channel(channel: str):
    raise HTTPException(404, f"Unknown event channel: {channel}")
