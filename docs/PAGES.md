# Vitals — Page Guide

A detailed walkthrough of every page in the application: what it shows, who can
open it, what each control does, and which API endpoints power it.

Roles: **Administrator** (admin), **Clinician**, **Front desk**, **Manager**.
Administrators pass every role check. The sidebar only shows pages the signed-in
role can use, and the API enforces the same rules server-side regardless of
what the client renders.

---

## Login — `/login`

**Access:** public.

Sign-in screen. The left panel (desktop only) summarizes the six product areas;
the right card holds the form.

- **Email / Password** — credentials are exchanged at `POST /api/auth/login` for
  an access token (60 min) and refresh token (7 days). Both are kept in
  localStorage; every API call carries the access token, and a 401 triggers one
  silent refresh (`POST /api/auth/refresh`) before the user is logged out.
- **Error line** — invalid credentials render "Invalid email or password."
  inline; other failures suggest checking that the API is running.
- **Demo accounts (dev only)** — in development builds a dashed section lists
  the four seeded accounts (Administrator, Clinician, Front desk, Manager). One
  click fills the form; nothing auto-submits. The block is compiled out of
  production builds (`import.meta.env.DEV`).
- **Brute-force lockout** — five failed attempts lock the account for 15
  minutes (HTTP 429 with the remaining wait); a successful login resets the
  counter.
- **Create an account** — links to `/register`. **Forgot password?** — links
  to the reset flow below.

## Forgot / reset password — `/forgot-password`, `/reset-password`

Requesting a reset always shows the same acknowledgement (no user
enumeration). When the account exists, a **single-use token valid for one
hour** is minted — without email infrastructure the reset link is written to
the backend server log. The reset page consumes the token, sets the new
password, clears any lockout, and revokes every session.

After sign-in, the user lands on `/` (see *Landing behavior* below).

## Register — `/register`

**Access:** public.

Account creation via `POST /api/auth/register`. Fields: name, email, **role**
(Clinician, Front desk or Manager — administrator accounts can only be seeded
or created server-side), and a password of at least 8 characters (bcrypt-hashed
server-side). Success signs the user straight in.

---

## Landing behavior — `/`

- **Clinician / Front desk** → redirected to `/patients`.
- **Manager / Administrator** → the Population dashboard renders in place.

## App shell (all signed-in pages)

- **Sidebar** — role-filtered navigation. On desktop the hamburger collapses it
  to an icon rail (remembered across reloads); on mobile it becomes a drawer.
  The footer shows the signed-in user and role, and a reminder that all data is
  synthetic.
- **Topbar search** — visible to clinicians and front desk. Typing two or more
  characters queries `GET /api/search?q=…` (debounced 250 ms) and shows grouped
  results: **Patients** (matched on first/last name, full name, or MRN) and
  **Encounters** (matched on reason/notes — clinicians and admins only; front
  desk never sees clinical rows). Records the caller cannot open under consent
  rules are filtered out server-side. Clicking any hit navigates to that
  patient's record.
- **Notifications bell** — unread badge and a dropdown of recent alerts
  (opening marks them read). Notifications are generated when someone else
  books, moves or cancels one of your appointments, and when newly recorded
  observations push a patient into the high-risk band. A dedicated SSE
  channel keeps the badge live.
- **Theme toggle** — light/dark, remembered in localStorage.
- **User menu** — shows name/email; **Sign out** clears credentials and the API
  cache.
- **Errors** — every route has an error boundary that renders inside the shell
  (with Go back / Home actions) instead of a blank screen; unknown URLs show a
  404 variant.

---

## Population dashboard — `/`

**Access:** Manager, Administrator (`GET /api/dashboard`).

Population-level measures over the whole active patient base (merged duplicate
tombstones are excluded):

- **Stat tiles** — total patients, encounters, observations, and upcoming
  booked appointments.
- **Encounters per month / Observations per month** — area charts of the
  trailing six calendar months, zero-filled so quiet months stay visible.
- **Age distribution** — counts in bands 0–17, 18–39, 40–64, 65+.
- **Sex** and **Patients by source** — how the population splits by recorded
  sex and by originating system (manual, CSV import, HL7 feed, FHIR import).
  Every bar carries its value as a direct label.
- **Risk flag summary line** — how many patients are flagged, split into high
  and moderate, with a note explaining the method (rule-based score over each
  patient's latest observations, flag threshold ≥ 3).
- **Risk flags table** (`GET /api/dashboard/risk-flags`, paginated) — one row
  per flagged patient: name → links to the record, age, a badge with level and
  score, and **the full list of rules that fired**, each with the measured
  value and its point contribution (e.g. *"Elevated systolic blood pressure:
  152 mmHg (+2)"*). This is the explainability guarantee: no flag exists
  without human-readable reasons.

Scoring rules cover systolic/diastolic blood pressure, fasting glucose, HbA1c,
BMI, oxygen saturation, resting heart rate, and age ≥ 65. Score ≥ 3 flags a
patient (moderate); ≥ 6 is high.

## Patients — `/patients`

**Access:** Clinician, Front desk, Administrator (`GET /api/patients`).

The patient registry, server-paginated (20 per page).

- **Search box** — matches first/last/full name, MRN identifier, phone or
  email as you type (page resets on every keystroke).
- **Sort** — by name, date of birth, or newest first (whitelisted
  server-side).
- **Table** — name with computed age, MRN, date of birth, sex, phone, current
  **risk level** (computed per request by the rule engine), and a source
  badge. Clicking a row opens the record.
- **New patient** (clinicians/admins only) — modal with demographics (first and
  last name, date of birth, sex), contact fields, address, and free-text
  medical history. Validation: the date of birth cannot be in the future; MRNs
  are auto-generated (`MRN-XXXXXXXX`) when not supplied and must be unique.
  Creates via `POST /api/patients` and is audited.

## Patient record — `/patients/:id`

**Access:** Clinician, Front desk, Administrator — subject to consent rules.
Opening a record is itself an audited event (`patient.viewed`).

If the record is **restricted** and the caller has no grant, the API returns
403 and the page shows *"Access to this record is restricted by consent
rules"* — and the denial is written to the audit log.

Header: patient name, a red **Restricted** badge when consent rules are active,
the record's source badge, **Export FHIR** and **Edit** (clinicians/admins).

- **Demographics card** — MRN, date of birth with age, sex, phone, email,
  address.
- **Medical history card** — the free-text history, or an empty state.
- **Edit** — same modal as creation, via `PUT /api/patients/:id` (audited).
- **Export FHIR** — downloads `<MRN>-fhir-bundle.json`, a FHIR R4 collection
  Bundle containing the Patient resource (MRN identifier, name, birthDate,
  gender, telecom, address) plus one LOINC-coded Observation resource per
  stored observation (`GET /api/patients/:id/fhir`, audited).

Clinicians and administrators also see:

- **Clinical lists card** (`GET /api/patients/:id/clinical-lists`) — three
  structured sections, each with inline add forms and per-row actions, all
  audited:
  - **Problem list** — condition description, optional ICD-10 code and onset
    date, with an active/resolved status toggle and remove action.
  - **Medications** — name, dose and frequency with an active/stopped badge, a
    stop action, and remove.
  - **Allergies** — substance, optional reaction, and severity (mild /
    moderate / severe, color-coded).
  These feed the risk engine: active chronic conditions on the problem list
  and polypharmacy (5+ active medications) add explainable points to the
  patient's risk score, and all three lists export as FHIR resources
  (Condition, MedicationStatement, AllergyIntolerance) in the bundle.
- **Vitals trends card** (`GET /api/patients/:id/observations/trends`) —
  small-multiple line charts, one per measure with two or more recorded
  values (heart rate, blood pressure, glucose, HbA1c, …), latest value in
  each header. One measure per chart; never a dual axis.
- **Imaging & documents card** (`GET/POST /api/patients/:id/attachments`) —
  PNG/JPEG/PDF/DICOM uploads up to 10 MB, tagged *imaging* or *document*
  with a description. Files preview inline (images and PDFs via an
  authenticated blob fetch), download, and delete. Uploads, views and
  removals are all audited and consent-gated.
- **Timeline card** (`GET /api/patients/:id/timeline`, paginated) — one
  chronological stream, newest first, merging encounters (with observation
  counts and clinician), appointments (with status), and every
  problem/medication/allergy change, each with a kind icon and source badge.

- **Encounters card** (paginated, 10 per page) — every encounter, newest first:
  type, reason, timestamp, documenting clinician, observation count, source
  badge. Rows expand in place to show each observation (code, value with unit,
  time) and the visit notes.
  - **New encounter** — modal with date/time, type (office visit, admission,
    telehealth), reason, notes, and a dynamic list of observation rows. Each
    row picks a code from the observation catalog (`GET
    /api/observations/catalog`) — heart rate, blood pressure, temperature,
    respiratory rate, SpO₂, weight, height, BMI, glucose, HbA1c, or a text
    note — and shows the plausible range as the input placeholder. The server
    validates every value for **type** (numeric vs text) and **physiologic
    range**, rejecting the whole encounter with a specific message (e.g.
    *"Heart rate of 900.0 bpm is above the plausible range (20–300)"*).
- **Consolidated record card** (`GET /api/patients/:id/summary`) — the
  cross-source view:
  - a duplicate warning banner when pending duplicate flags touch this record,
    linking to `/duplicates`;
  - **Contributing sources** — each source system with its encounter and
    observation counts;
  - **Latest observations (all sources)** — the most recent value per
    observation code across every system, each tagged with the source it came
    from and its timestamp.

Administrators additionally see:

- **Consent & access rules card** (`GET/PUT /api/patients/:id/consent`) — a
  toggle marks the record restricted. While restricted, only administrators
  and the listed grantees may open it. Grants are added by **role** (clinician,
  front desk, manager) or by **user** (email, resolved to the account) and can
  be removed individually. Every change is audited (`consent.updated`); every
  blocked read is audited (`access.denied`).

## Appointments — `/appointments`

**Access:** Clinician, Front desk, Administrator (`GET /api/appointments`).

Two views, toggled in the header: the **day list** and a **week grid**.

The week grid shows one clinician at a time across seven day columns and
clinic hours (8:00–18:00): appointment blocks are positioned by time and
colored by status, today is highlighted, and clicking a booked block opens
the reschedule modal (`GET /api/appointments/week`).

The booking modal includes **Find next free slot**
(`GET /api/appointments/next-free`): it scans the chosen clinician's booked
schedule on 15-minute boundaries inside clinic hours — up to two weeks ahead
— and fills the form with the first gap long enough for the requested
duration.

The day list is paginated at 50.

- **Day controls** — previous/next arrows, a date picker, and a Today shortcut.
- **Clinician filter** — restrict the list to one clinician (the *daily
  schedule per clinician* view); options come from
  `GET /api/appointments/clinicians`.
- **Status filter** — booked, completed, or cancelled.
- **Table** — time range, patient (linked, with MRN), clinician, reason, and a
  status badge. Booked rows offer three actions:
  - **✓ Mark completed** — `POST /api/appointments/:id/status`.
  - **⟳ Move / reschedule** — modal pre-filled with the appointment; change
    clinician, date, times, or reason (`PUT /api/appointments/:id`).
  - **✕ Cancel** — confirmation dialog, then a status change to cancelled.
    Cancelled appointments cannot be moved afterwards; a new one must be
    booked.
- **Book appointment** — modal with a patient picker (search by name or MRN,
  then choose from matches), clinician, date, start/end time, and reason
  (`POST /api/appointments`).

The server rejects bookings and moves whose time slot **overlaps another booked
appointment for the same clinician**, and end times at or before the start.
Booking, moving, cancelling and completing are all audited.

## Duplicates — `/duplicates`

**Access:** Clinician, Administrator.

Review queue for possible duplicate identities across source systems.

- **Scan for duplicates** (`POST /api/duplicates/scan`) — flags pairs of active
  records whose normalized name + date of birth match (exact first/last name,
  or same last name + first initial). The reason string records which
  heuristic matched and whether the pair crosses sources. Already-reviewed
  pairs are never re-flagged.
- **Status filter** — pending review (default), merged, dismissed, or all.
- **Pair list** (paginated) — each row shows the two records side by side
  (**Keep** vs **Candidate duplicate**) with name, MRN, date of birth, sex and
  source badges, plus the match reason. Pending pairs offer:
  - **Merge** (`POST /api/duplicates/:id/merge`, with confirmation) — moves all
    encounters, observations and appointments onto the surviving record, fills
    any missing contact/history fields from the absorbed one, resolves other
    flags touching the absorbed record, and leaves it as a hidden tombstone
    (excluded from lists, search, scans and analytics). Audited as
    `patients.merged`.
  - **Not a duplicate** (`POST /api/duplicates/:id/dismiss`) — keeps both
    records and remembers the decision.

## Import — `/import`

**Access:** Administrator only (the integrator role).

Three ingestion cards, one shared rulebook: patients match by MRN (existing
demographics are never overwritten by an import), observations validate against
the same catalog as manual entry, imported observations land under a new
encounter tagged with the source system, and **every record that fails mapping
becomes a reported issue — nothing is silently dropped**.

- **CSV file** (`POST /api/imports/csv`) — upload or paste rows with header
  `mrn, first_name, last_name, dob` plus optional `sex, code, value, taken_at`.
  A row without observation columns just upserts the patient. Dates accept
  ISO, `YYYYMMDD`, and `MM/DD/YYYY` forms. A "Use sample" button fills a
  working example.
- **HL7-style messages** (`POST /api/imports/hl7`) — paste pipe-delimited
  segments: `MSH` is ignored, `PID|mrn|Family^Given|YYYYMMDD|sex` starts a
  patient, `OBX|loinc|value|unit|timestamp` attaches an observation to the
  most recent PID by LOINC code. Per-line error reporting.
- **FHIR resources** (`POST /api/fhir/import`) — paste a FHIR R4 Bundle or a
  single Patient/Observation resource as JSON. Resources are validated against
  the actual FHIR schema (fhir.resources models) before mapping; observations
  are matched by LOINC code and take `valueQuantity` or `valueString`.

Each card reports its result inline (*imported X of Y records — N errors*).

- **Import history** (paginated) — one row per batch: timestamp, label, format
  badge, record/imported/error counts. Clicking a row opens the **mapping
  errors modal** (paginated): record number, the exact error message (e.g.
  *"Unknown LOINC code: '9999-9'"*), and the raw source data for that record.

All imports are audited with their counts.

## Reports — `/reports`

**Access:** Manager, Administrator (`GET /api/reports/cohort`).

Cohort builder with export.

- **Filters** — minimum/maximum age, sex, source system, and risk level (any,
  flagged at any level, high, moderate). The preview updates live and resets
  to page one on any filter change.
- **Privacy note** — states explicitly whether the current caller gets the
  identified or de-identified column set.
- **Preview table** (paginated) — age, sex, source, encounter count, and risk
  badge for every cohort member; administrators additionally see the name and
  MRN column.
- **Export CSV** (`GET /api/reports/cohort/export`) — downloads
  `vitals-cohort-<date>.csv` with the same filters applied. Column sets are
  role-based and enforced server-side:
  - **Administrator:** mrn, first/last name, dob, age, sex, source, phone,
    email, encounters, risk score/level/reasons.
  - **Manager:** age, sex, source, encounters, risk score/level/reasons —
    name, MRN, date of birth and contact fields are **never emitted**, not
    merely hidden.
  Every export is audited with its filters and whether it was de-identified.

## Messages — `/messages`

**Access:** every signed-in role.

Internal email-style messaging between staff.

- **Tabs** — **Inbox** (unread count pill + unread-only filter), **Archived**
  and **Sent**, all paginated (`GET /api/messages/inbox`, `?archived=true`,
  `/api/messages/sent`). Unread rows show a dot and bold subject; rows with
  attachments show a paperclip.
- **New message** (`POST /api/messages`) — a checkbox picker selects **any
  number of recipients** (each gets their own copy and conversation, like
  BCC), subject, body, an optional **patient link** (clinical/front-desk
  roles), and up to **three attachments** (PNG/JPEG/PDF/TXT/CSV, 5 MB each).
  Sends are audited per recipient.
- **Archive** — recipients can archive a message out of the inbox (and
  restore it); the sender's view is unaffected and unread counts skip
  archived mail.
- **Thread view** — chat-style bubbles (yours right-aligned); opening marks
  your unread messages read. A linked patient shows as a badge that jumps to
  the record; attachments render as download chips (participants only). The
  **reply** box addresses the other participant automatically, prefixes
  `Re:`, and stays in the same thread (replies inherit the patient link).
- **Live badges** — the sidebar Messages entry and topbar mail icon update
  in real time: the app shell holds one SSE connection
  (`GET /api/events/messages`) that signals when your mail state changes,
  invalidating the message caches — no interval polling.

## Profile — `/profile`

**Access:** every signed-in role (via the user menu in the topbar).

- **Profile card** (`PUT /api/auth/profile`) — edit the display name and
  upload a **profile photo** (PNG/JPEG; the browser cover-crops it to a
  256 px square JPEG before upload, and the server validates the data URL
  and enforces a 300 KB cap). Email and role are shown read-only. Saving
  updates the sidebar and topbar immediately — photos replace the initial
  avatars everywhere.
- **Password card** (`POST /api/auth/change-password`) — requires the
  current password and a confirmed new one (min. 8 characters). A
  successful change **revokes every other session's refresh token**, so
  stolen or forgotten logins die with the old password.
- **Sessions card** (`POST /api/auth/logout-all`) — **Sign out everywhere**
  (with confirmation) ends every active session on every device, including
  the current one: all refresh tokens are revoked *and* a server-side cutoff
  invalidates access tokens issued before that moment, so other devices are
  signed out on their very next request — not up to an hour later when their
  token would have expired.

All three actions are audited (`user.profile_updated`,
`user.password_changed`, `auth.logout_all`).

## Users — `/users`

**Access:** Administrator only.

Account administration with search and pagination:

- **Role** — changed inline per user (admin, clinician, front desk, manager).
- **Deactivate / Reactivate** — a deactivated account is signed out
  everywhere immediately, cannot sign in, and disappears from clinician and
  message-recipient pickers; its historical records stay attributed.
- **Reset password** — issues a one-time temporary password (shown to the
  admin once) and signs the user out everywhere; it also clears any lockout.
- **Self-protection** — admins cannot change their own role, deactivate
  themselves, or reset their own password here.

All actions are audited (`user.role_changed`, `user.activated`,
`user.deactivated`, `user.password_reset_by_admin`).

## Audit log — `/audit`

**Access:** Administrator only (`GET /api/audit`).

The tamper-resistant activity trail. Entries are **insert-only**: no API path
exists to edit or delete them.

- **Filters** — by action (dropdown populated from the actions that actually
  occurred, `GET /api/audit/actions`) and by entity ID (paste a record's UUID
  to see its full history).
- **Table** (paginated) — timestamp, acting user's email, a color-coded action
  badge (creations green, updates amber, views blue, denials/cancellations
  red), the entity type and ID, and structured detail (JSON) where the action
  recorded extras (e.g. import counts, merge target, consent grant count).

Recorded actions include: `patient.viewed / created / updated`,
`encounters.viewed`, `encounter.created`, `observation.added`,
`appointment.booked / moved / completed / cancelled`, `import.csv / hl7 /
fhir`, `duplicates.scanned / dismissed`, `patients.merged`,
`patient.fhir_exported`, `consent.updated`, `access.denied`,
`report.exported`, `message.sent`, `problem.added / updated / removed`,
`medication.added / updated / removed`, `allergy.added / removed`,
`attachment.uploaded / viewed / removed`, `user.profile_updated`,
`user.password_changed`, `user.role_changed`, `user.activated / deactivated`,
and `user.password_reset_by_admin`.

---

## Access matrix

| Page | Admin | Clinician | Front desk | Manager |
|---|---|---|---|---|
| Dashboard `/` | ✓ | – | – | ✓ |
| Patients `/patients` | ✓ | ✓ | ✓ (no clinical cards) | – |
| Patient record `/patients/:id` | ✓ | ✓ (consent-gated) | demographics only (consent-gated) | – |
| Appointments `/appointments` | ✓ | ✓ | ✓ | – |
| Duplicates `/duplicates` | ✓ | ✓ | – | – |
| Import `/import` | ✓ | – | – | – |
| Messages `/messages` | ✓ | ✓ | ✓ | ✓ |
| Profile `/profile` | ✓ | ✓ | ✓ | ✓ |
| Users `/users` | ✓ | – | – | – |
| Reports `/reports` | ✓ (identified) | – | – | ✓ (de-identified) |
| Audit `/audit` | ✓ | – | – | – |
| Topbar search | ✓ | ✓ | ✓ (patients only) | – |

---

## Sessions & security

Signing in returns a short-lived access token (kept client-side) while the
refresh token lives only in an **httpOnly SameSite=Lax cookie** scoped to
`/api/auth` — JavaScript never sees it. Every refresh **rotates** the token
server-side; replaying a rotated token is treated as theft and revokes every
session for that user. Logout revokes the token and clears the cookie.
Access tokens carry an issued-at claim checked against a per-user
revocation cutoff, which is how **Sign out everywhere** takes effect
immediately rather than at token expiry.

## Testing & tooling

- **Backend:** `pytest` (45 tests) over the service layer on a dedicated test
  database — ingestion mapping, risk rules, duplicates, consent, token
  rotation, messaging — plus RBAC checks over HTTP. Run from `backend/` with
  `.venv/bin/python -m pytest tests`.
- **End-to-end:** `frontend/e2e/` holds a Playwright suite (`npm run e2e`, 15
  tests) covering login/registration, patient creation and validation,
  encounters, appointments, cross-session messaging with reply, archiving,
  attachment upload/preview, trends, and per-role RBAC. It reuses running dev
  servers and the seeded database.
- **CI:** GitHub Actions runs backend tests, frontend lint/typecheck/build,
  and the full e2e suite on every push/PR.
- **Docker:** `docker compose up` brings up Postgres, the migrated API and an
  nginx-served frontend build (seed with
  `docker compose exec backend python seed.py`).
- **Research evaluation:** `python -m evaluation.run` (from `backend/`)
  regenerates [EVALUATION.md](EVALUATION.md) — duplicate-detection
  precision/recall on synthetic corrupted feeds, and the explainable-rules vs
  logistic-regression benchmark.
