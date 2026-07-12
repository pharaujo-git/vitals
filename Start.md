# Vitals

A health information system with clinical data integration and light analytics.

**Folder and repository name:** vitals

**Date:** July 9, 2026

**Scope:** this is a simpler, applied project than Argus, Nimbus, and Verity. It is a solid system with one focused research angle, so it is faster to build while still attracting a health informatics professor.

**Target programs and professors:** best fit first.
- FAU: Taghi Khoshgoftaar (health informatics and medical big data analytics, and he funds and graduates many students), the strongest fit. Xingquan Zhu (biomedical decision support), Oge Marques (medical imaging, if you add an imaging feature).
- UNC Charlotte: Yaorong Ge and Lixia Yao of the Health Informatics Lab, whose listed work includes clinical data integration and data warehousing, which lines up with your integration background.
- FIU: Christian Poellabauer (digital health and mobile sensing), plus the health informatics program.

**Suggested stack:** Python and FastAPI, Postgres through SQLAlchemy with Alembic migrations, the fhir.resources library for the health data standard, pandas and scikit-learn for simple analytics and risk flags, JWT authentication through python-jose and passlib, and a React frontend.

## React Frontend

You should follow the layout that is in this folder: `/Users/pharaujo/Git/PersonalFinance/frontend`

## Description

Vitals is a health information system: patient records, appointments, and clinical observations, with a consolidated patient view built by pulling data from several source formats into one store. On top of that it speaks the health data standard, FHIR, so records can be imported and exported in a portable form, and it shows a simple dashboard of population health measures with lightweight risk flags.

The reason Vitals fits your list is that its heart is clinical data integration, which is exactly the kind of heterogeneous data consolidation you already do with billing and ERP systems, now applied to health. Clinical data integration and data warehousing is a listed research area of the Health Informatics Lab at UNC Charlotte, and health informatics and medical big data are core to Dr. Khoshgoftaar's work at FAU. Because it is applied and contained, Vitals is a good choice when you want a strong project without the size of a research platform.

## Features and User Stories

### US-1: Patient records
As a clinician, I want to create and update patient records, so that I have a reliable place for demographics and history.
Acceptance criteria:
- A patient can be created, edited, and searched.
- Each record has demographics, history, and a list of encounters.

### US-2: Appointments and scheduling
As a front desk user, I want to schedule and manage appointments, so that visits are organized.
Acceptance criteria:
- Appointments can be booked, moved, and cancelled.
- A daily schedule can be viewed per clinician.

### US-3: Clinical observations
As a clinician, I want to record observations such as vital signs and notes during an encounter, so that the visit is documented.
Acceptance criteria:
- Observations are attached to an encounter and a patient.
- Values are validated for type and range.

### US-4: Multi source data ingestion
As an integrator, I want to import clinical data from several source formats into one store, so that a patient's data is consolidated.
Acceptance criteria:
- At least two source formats, for example comma separated files and a simple message format, can be imported.
- Records are mapped into the common model, and mapping errors are reported, not dropped.

### US-5: FHIR import and export
As an integrator, I want to import and export records in the FHIR standard, so that data is portable across systems.
Acceptance criteria:
- A patient and their observations can be exported as FHIR resources.
- Valid FHIR resources can be imported and mapped into the store.

### US-6: Consolidated patient view
As a clinician, I want one consolidated view of a patient across all sources, so that I do not miss information.
Acceptance criteria:
- The view merges records from different sources for the same patient.
- Duplicate records are detected and flagged for review.

### US-7: Population dashboard and risk flags
As a manager, I want a dashboard of population measures with simple risk flags, so that I can see patterns and patients who may need attention.
Acceptance criteria:
- The dashboard shows counts and trends across the patient population.
- A simple rule or model flags patients above a risk threshold, and each flag is explainable.

### US-8: JWT login and roles
As a user, I want to log in with a JWT and hold a role, so that access is controlled.
Acceptance criteria:
- A login endpoint returns a signed token, and passwords are hashed.
- Roles such as clinician, front desk, and administrator limit what each user can do.

### US-9: Consent and access control
As a privacy officer, I want access to a record governed by consent and role, so that patient data is protected.
Acceptance criteria:
- A record can be marked with access rules.
- Access outside the rules is denied and recorded.

### US-10: Audit log
As a privacy officer, I want an audit log of who viewed or changed a record, so that access is traceable.
Acceptance criteria:
- Views and changes to sensitive data are recorded with who and when.
- The log cannot be edited through the normal interface.

### US-11: Search
As a clinician, I want to search patients and encounters quickly, so that I can find information during a visit.
Acceptance criteria:
- Search works across name, identifier, and encounter.
- Results respect the caller's access rights.

### US-12: Reports and export
As a manager, I want to export a report of a cohort, so that I can share summaries.
Acceptance criteria:
- A filtered cohort can be exported to a file.
- The export excludes fields the user is not allowed to see.

## Persistence and Safety

- Postgres is the primary datastore, behind a repository layer, with Alembic migrations.
- All access requires authentication, and secrets never live in the code.
- Sample data is synthetic, so no real patient data is used during development.

## Research Angle

Keep the research focused so the project stays simple. Two good options, either of which a professor can grow:
- Clinical data integration and interoperability: how cleanly heterogeneous sources map into one FHIR based model, and how well duplicates are resolved. This fits Dr. Ge and Dr. Yao at UNC Charlotte and reuses your integration strength.
- Lightweight decision support: whether a simple, explainable risk flag helps without overwhelming clinicians. This fits Dr. Khoshgoftaar and Dr. Zhu at FAU.

## Roadmap

- Phase 1: patient records, appointments, observations, JWT login with roles, and search. This alone is a working system.
- Phase 2: multi source ingestion, the consolidated patient view with duplicate detection, and the audit log.
- Phase 3: FHIR import and export, and the population dashboard with explainable risk flags.
- Phase 4: consent based access control, cohort reports, and a short evaluation of the chosen research angle.

## Alternative

The same shape works as a business system if you prefer, for example a small ERP or inventory system with a process mining or analytics angle, which would fit information systems and business analytics faculty. The health version is the stronger academic fit, because health informatics is well funded and several professors on your list work in it.

## Conclusion

Vitals is your simpler, applied project. It reuses your data integration strength, it maps to funded health informatics professors at FAU, UNC Charlotte, and FIU, and it can be built and shown without the scope of a full research platform. The strongest fits are Dr. Khoshgoftaar at FAU in Boca Raton and Dr. Ge and Dr. Yao at UNC Charlotte.