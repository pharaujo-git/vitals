from fastapi import FastAPI

from app.api.routers import (
    appointments,
    audit,
    auth,
    duplicates,
    encounters,
    imports,
    patients,
    search,
)

app = FastAPI(title="Vitals API", version="0.1.0")

app.include_router(auth.router, prefix="/api")
app.include_router(patients.router, prefix="/api")
app.include_router(appointments.router, prefix="/api")
app.include_router(encounters.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(imports.router, prefix="/api")
app.include_router(duplicates.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
