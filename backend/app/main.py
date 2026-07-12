import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routers import (
    appointments,
    attachments,
    audit,
    auth,
    clinical,
    dashboard,
    duplicates,
    encounters,
    events,
    fhir,
    imports,
    messages,
    notifications,
    patients,
    reports,
    search,
    users,
)

# Surface app loggers (e.g. the dev password-reset link) on the console.
logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(message)s")

app = FastAPI(title="Vitals API", version="0.1.0")

app.include_router(auth.router, prefix="/api")
app.include_router(patients.router, prefix="/api")
app.include_router(appointments.router, prefix="/api")
app.include_router(encounters.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(imports.router, prefix="/api")
app.include_router(duplicates.router, prefix="/api")
app.include_router(fhir.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(messages.router, prefix="/api")
app.include_router(clinical.router, prefix="/api")
app.include_router(attachments.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Single-service deploys: serve the built SPA next to the API when present
# (STATIC_DIR is baked by the root Dockerfile; absent in local dev, where
# Vite serves the frontend and proxies /api here).
_static_dir = Path(os.environ.get("STATIC_DIR", "static"))
if _static_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=_static_dir / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(404, "Not found")
        candidate = _static_dir / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_static_dir / "index.html")
