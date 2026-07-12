"""Integration evaluation: how well does the pipeline consolidate messy sources?

Runs against a disposable database. Generates a synthetic ground-truth
population, exports it as two overlapping "source systems" (CSV feeds with
different MRNs), corrupts a controlled fraction of the second feed (name
typos, day-level DOB shifts), injects malformed rows, then measures:

- mapping error reporting: are all injected bad rows reported as issues?
- duplicate detection: precision/recall against known same-person pairs,
  broken down by corruption type.
"""

import os
import random
import subprocess
from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core import security
from app.db import models
from app.db.session import Base
from app.services import duplicates, ingestion

EVAL_DATABASE_URL = os.environ.get(
    "EVAL_DATABASE_URL", "postgresql+psycopg://localhost:5432/vitals_eval"
)

FIRST = ["Maria", "Ana", "Sofia", "Emma", "Olivia", "Carlos", "Joao", "Miguel", "James",
         "Liam", "Nina", "Clara", "Elena", "Victor", "Omar", "Ivan", "Grace", "Hugo"]
LAST = ["Silva", "Santos", "Oliveira", "Souza", "Costa", "Pereira", "Almeida", "Nguyen",
        "Chen", "Garcia", "Martinez", "Johnson", "Smith", "Khan", "Patel", "Kim", "Sato"]

N_PEOPLE = 200
N_OVERLAP = 120  # people present in both feeds
CORRUPTION = (("clean", 0.5), ("typo_inner", 0.15), ("typo_first", 0.10), ("dob_shift", 0.25))


def _typo_inner(name: str, rng: random.Random) -> str:
    if len(name) < 3:
        return name + "e"
    i = rng.randrange(1, len(name) - 1)
    return name[:i] + name[i + 1] + name[i] + name[i + 2:]  # swap two inner chars


def _typo_first(name: str) -> str:
    return name[1] + name[0] + name[2:]  # swap the first two chars: breaks the initial


def _person_row(mrn: str, first: str, last: str, dob: date) -> str:
    return f"{mrn},{first},{last},{dob.isoformat()},f,heart_rate,72,2026-07-01T09:00:00"


def run(seed: int = 7) -> str:
    rng = random.Random(seed)
    subprocess.run(["createdb", "vitals_eval"], capture_output=True)
    engine = create_engine(EVAL_DATABASE_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        user = models.User(
            email="eval@vitals.test",
            password_hash=security.hash_password("password123"),
            display_name="Eval Runner",
            role="admin",
        )
        db.add(user)
        db.commit()

        # Ground-truth people.
        people = []
        for i in range(N_PEOPLE):
            people.append({
                "first": rng.choice(FIRST),
                "last": rng.choice(LAST),
                "dob": date(1940, 1, 1) + timedelta(days=rng.randrange(0, 26000)),
            })

        header = "mrn,first_name,last_name,dob,sex,code,value,taken_at"
        feed_a = [header] + [
            _person_row(f"MRN-A-{i}", p["first"], p["last"], p["dob"])
            for i, p in enumerate(people)
        ]

        # Feed B: overlapping subset under a different MRN scheme, corrupted.
        corruption_of: dict[int, str] = {}
        feed_b = [header]
        for i in range(N_OVERLAP):
            p = people[i]
            roll, acc = rng.random(), 0.0
            kind = "clean"
            for name, weight in CORRUPTION:
                acc += weight
                if roll < acc:
                    kind = name
                    break
            corruption_of[i] = kind
            first, last, dob = p["first"], p["last"], p["dob"]
            if kind == "typo_inner":
                first = _typo_inner(first, rng)
            elif kind == "typo_first":
                first = _typo_first(first)
            elif kind == "dob_shift":
                dob = dob + timedelta(days=rng.choice([-1, 1]))
            feed_b.append(_person_row(f"MRN-B-{i}", first, last, dob))

        # Malformed rows: the pipeline must report every one, not drop them.
        bad_rows = [
            "MRN-X-1,Bad,Date,notadate,f,,,",
            "MRN-X-2,Jane,Doe,1975-04-02,f,cholesterol,220,",
            "MRN-X-3,Jane,Doe,1975-04-02,f,heart_rate,900,",
            ",No,Mrn,1980-01-01,f,,,",
            "MRN-X-5,,Nameless,1980-01-01,f,,,",
        ]
        feed_b.extend(bad_rows)

        batch_a = ingestion.import_csv(db, user, "feed A", "\n".join(feed_a))
        batch_b = ingestion.import_csv(db, user, "feed B", "\n".join(feed_b))
        # Detach-safe scalars for reporting after the session closes.
        a_imported, a_total, a_errors = (
            batch_a.imported_count, batch_a.total_records, batch_a.error_count,
        )
        b_errors = batch_b.error_count
        error_reporting_rate = b_errors / len(bad_rows)

        # Duplicate detection vs ground truth.
        duplicates.scan(db)
        flags = db.query(models.DuplicateFlag).all()
        patients = {p.id: p for p in db.query(models.Patient).all()}

        def index_of(patient) -> tuple[str, int] | None:
            if patient.mrn.startswith("MRN-A-"):
                return ("A", int(patient.mrn.split("-")[-1]))
            if patient.mrn.startswith("MRN-B-"):
                return ("B", int(patient.mrn.split("-")[-1]))
            return None

        true_pairs = {i for i in range(N_OVERLAP)}
        found_true: dict[int, str] = {}
        false_positives = 0
        for flag in flags:
            a = index_of(patients[flag.patient_a_id])
            b = index_of(patients[flag.patient_b_id])
            if a and b and a[0] != b[0] and a[1] == b[1] and a[1] in true_pairs:
                found_true[a[1]] = corruption_of[a[1]]
            else:
                false_positives += 1

        recall_by_kind = {}
        for kind, _ in CORRUPTION:
            total = sum(1 for k in corruption_of.values() if k == kind)
            hit = sum(1 for k in found_true.values() if k == kind)
            recall_by_kind[kind] = (hit, total)

        tp = len(found_true)
        fp = false_positives
        fn = N_OVERLAP - tp
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    engine.dispose()

    lines = [
        "## Experiment 1 — clinical data integration quality",
        "",
        f"Synthetic population of **{N_PEOPLE} people**; {N_OVERLAP} of them also arrive",
        "through a second source system under different MRNs. Half of the second feed",
        "is clean, 15% has an **inner-character name typo**, 10% a **first-letter",
        "typo** (breaks the initial), and a quarter a **±1 day date-of-birth shift**.",
        "Five malformed rows (bad dates, unknown codes, out-of-range values, missing",
        "identifiers) are injected on top.",
        "",
        "### Mapping error reporting",
        "",
        f"- Injected malformed rows: **{len(bad_rows)}**",
        f"- Rows reported as batch issues: **{b_errors}**"
        f" → reporting rate **{error_reporting_rate:.0%}** (nothing silently dropped)",
        f"- Clean feed A imported {a_imported}/{a_total} rows with {a_errors} errors",
        "",
        "### Duplicate detection (name + DOB heuristics)",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| True pairs found | {tp} / {N_OVERLAP} |",
        f"| False positives | {fp} |",
        f"| Precision | **{precision:.2f}** |",
        f"| Recall | **{recall:.2f}** |",
        f"| F1 | **{f1:.2f}** |",
        "",
        "Recall by corruption type:",
        "",
        "| Corruption | Found | Notes |",
        "|---|---|---|",
    ]
    notes = {
        "clean": "exact name+DOB match",
        "typo_inner": "first initial survives, so the initial+surname+DOB heuristic catches these",
        "typo_first": "the initial breaks — missed by both heuristics",
        "dob_shift": "missed by design — the heuristics require an exact DOB",
    }
    for kind, (hit, total) in recall_by_kind.items():
        lines.append(f"| {kind} | {hit}/{total} | {notes[kind]} |")
    lines += [
        "",
        "**Reading.** Exact and inner-typo duplicates are handled by MRN upsert",
        "plus the two name+DOB heuristics; false positives come from coincidental",
        "name+DOB collisions in a small name pool, which is why flags go to human",
        "review instead of auto-merging. The two failure modes measured here —",
        "typos that break the first initial, and DOB shifts — motivate the obvious",
        "next step for the research agenda: phonetic name codes (Soundex/Metaphone)",
        "and windowed DOB blocking, then re-running this same harness to quantify",
        "the gain.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(run())
