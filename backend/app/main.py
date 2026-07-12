import logging

from fastapi import FastAPI

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


@app.get("/api/health")
def health():
    return {"status": "ok"}
