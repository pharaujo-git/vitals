# Vitals — Architecture

## Layers

```
React (features/*)  →  RTK Query (one base API, injected endpoints, SSE signals)
        │ /api (Vite proxy / nginx)
FastAPI routers     →  guard (RBAC + consent) → service → audit → response DTO
Services            →  business logic: ingestion, FHIR, risk rules, matching, …
Repositories        →  every SQLAlchemy query, shared Page/paginate helper
PostgreSQL          →  Alembic migrations (one per feature)
```

Dependency direction is one-way (routers → services → repositories → models);
services never import HTTP schemas, repositories never contain business rules.

## Entity-relationship diagram

```mermaid
erDiagram
    USER ||--o{ REFRESH_TOKEN : "sessions"
    USER ||--o{ PASSWORD_RESET_TOKEN : "resets"
    USER ||--o{ NOTIFICATION : "receives"
    USER ||--o{ MESSAGE : "sends / receives"
    USER ||--o{ ENCOUNTER : "documents"
    USER ||--o{ APPOINTMENT : "is booked as clinician"
    USER ||--o{ AUDIT_LOG : "acts"
    USER ||--o{ IMPORT_BATCH : "runs"
    USER ||--o{ ATTACHMENT : "uploads"

    PATIENT ||--o{ ENCOUNTER : "has"
    PATIENT ||--o{ OBSERVATION : "has"
    PATIENT ||--o{ APPOINTMENT : "has"
    PATIENT ||--o{ PROBLEM : "problem list"
    PATIENT ||--o{ MEDICATION : "medications"
    PATIENT ||--o{ ALLERGY : "allergies"
    PATIENT ||--o{ ATTACHMENT : "imaging / documents"
    PATIENT ||--o{ CONSENT_GRANT : "access rules"
    PATIENT ||--o{ DUPLICATE_FLAG : "candidate pairs"
    PATIENT |o--o{ MESSAGE : "linked in"
    PATIENT |o--o| PATIENT : "merged_into (tombstone)"

    ENCOUNTER ||--o{ OBSERVATION : "contains"
    MESSAGE ||--o{ MESSAGE_ATTACHMENT : "carries"
    MESSAGE |o--o{ MESSAGE : "thread (root_id / parent_id)"
    IMPORT_BATCH ||--o{ IMPORT_ISSUE : "reports"

    PATIENT {
        uuid id PK
        string mrn UK
        string first_name
        string last_name
        date dob
        string sex
        string source "manual|csv|hl7|fhir"
        bool restricted
        uuid merged_into_id FK
    }
    ENCOUNTER {
        uuid id PK
        uuid patient_id FK
        uuid clinician_id FK
        datetime occurred_at
        string encounter_type
        string source
    }
    OBSERVATION {
        uuid id PK
        uuid patient_id FK
        uuid encounter_id FK
        string code "catalog + LOINC"
        float value_num
        string value_text
        datetime taken_at
        string source
    }
    APPOINTMENT {
        uuid id PK
        uuid patient_id FK
        uuid clinician_id FK
        datetime start_at
        datetime end_at
        string status "booked|completed|cancelled"
    }
    MESSAGE {
        uuid id PK
        uuid sender_id FK
        uuid recipient_id FK
        uuid patient_id FK
        uuid root_id "conversation"
        uuid parent_id FK
        datetime read_at
        datetime archived_at
    }
    USER {
        uuid id PK
        string email UK
        string role "admin|clinician|front_desk|manager"
        bool active
        int failed_logins
        datetime locked_until
    }
    AUDIT_LOG {
        uuid id PK
        uuid user_id FK
        string action
        string entity_type
        string entity_id
        jsonb detail
    }
    DUPLICATE_FLAG {
        uuid id PK
        uuid patient_a_id FK
        uuid patient_b_id FK
        string reason
        string status "pending|merged|dismissed"
    }
```

## Cross-cutting mechanics

- **Auth** — short-lived JWT access token client-side; refresh token only in
  an httpOnly cookie with server-side rotation state and reuse detection.
- **RBAC** — `require_roles(...)` dependencies per endpoint; admin passes all.
- **Consent** — `ensure_access` gate on every patient-record read/write;
  denials are 403 and audited.
- **Audit** — insert-only trail written from controllers after each sensitive
  view/change.
- **Pagination** — every growable list returns `Page[T]`
  (`items/total/limit/offset`); repositories share one `paginate` helper.
- **Real-time** — SSE channels emit change *signals* from cheap per-user
  fingerprints (messages, notifications); clients refetch through their
  normal queries.
- **Ingestion** — CSV / HL7-style / FHIR all map through the same validation
  (observation catalog, MRN upsert) with per-record error reporting.
- **Duplicate matching** — four explainable tiers (exact, initial,
  edit-distance ≤ 2 blocked by DOB, DOB window ≤ 31 days on exact names),
  measured in [EVALUATION.md](EVALUATION.md).
