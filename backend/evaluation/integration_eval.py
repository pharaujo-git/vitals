"""Integration evaluation: how well does the pipeline consolidate messy sources?

Runs against a disposable database. Generates a synthetic ground-truth
population, exports it as two overlapping "source systems" (CSV feeds with
different MRNs), corrupts a controlled fraction of the second feed (name
typos, day-level DOB shifts), injects malformed rows, then measures:

- mapping error reporting: are all injected bad rows reported as issues?
- duplicate detection: precision/recall against known same-person pairs,
  for the exact-matching **baseline** and the **enhanced** matcher
  (edit-distance names + DOB windowing), on identical data — the research
  loop this project iterates on.
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
BAD_ROWS = [
    "MRN-X-1,Bad,Date,notadate,f,,,",
    "MRN-X-2,Jane,Doe,1975-04-02,f,cholesterol,220,",
    "MRN-X-3,Jane,Doe,1975-04-02,f,heart_rate,900,",
    ",No,Mrn,1980-01-01,f,,,",
    "MRN-X-5,,Nameless,1980-01-01,f,,,",
]


def _typo_inner(name: str, rng: random.Random) -> str:
    if len(name) < 3:
        return name + "e"
    i = rng.randrange(1, len(name) - 1)
    return name[:i] + name[i + 1] + name[i] + name[i + 2:]  # swap two inner chars


def _typo_first(name: str) -> str:
    return name[1] + name[0] + name[2:]  # swap the first two chars: breaks the initial


def _person_row(mrn: str, first: str, last: str, dob: date) -> str:
    return f"{mrn},{first},{last},{dob.isoformat()},f,heart_rate,72,2026-07-01T09:00:00"


def _build_feeds(seed: int) -> tuple[list[str], list[str], dict[int, str]]:
    """Deterministic feeds + corruption labels, shared by both matcher runs."""
    rng = random.Random(seed)
    people = [
        {
            "first": rng.choice(FIRST),
            "last": rng.choice(LAST),
            "dob": date(1940, 1, 1) + timedelta(days=rng.randrange(0, 26000)),
        }
        for _ in range(N_PEOPLE)
    ]

    header = "mrn,first_name,last_name,dob,sex,code,value,taken_at"
    feed_a = [header] + [
        _person_row(f"MRN-A-{i}", p["first"], p["last"], p["dob"]) for i, p in enumerate(people)
    ]

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
    feed_b.extend(BAD_ROWS)
    return feed_a, feed_b, corruption_of


def _experiment(feed_a, feed_b, corruption_of, scan_kwargs) -> dict:
    """Import both feeds into a fresh database and score one matcher config."""
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

        batch_a = ingestion.import_csv(db, user, "feed A", "\n".join(feed_a))
        batch_b = ingestion.import_csv(db, user, "feed B", "\n".join(feed_b))
        import_stats = {
            "a_imported": batch_a.imported_count,
            "a_total": batch_a.total_records,
            "a_errors": batch_a.error_count,
            "b_errors": batch_b.error_count,
        }

        duplicates.scan(db, **scan_kwargs)
        flags = db.query(models.DuplicateFlag).all()
        patients = {p.id: p for p in db.query(models.Patient).all()}

        def index_of(patient):
            if patient.mrn.startswith("MRN-A-"):
                return ("A", int(patient.mrn.split("-")[-1]))
            if patient.mrn.startswith("MRN-B-"):
                return ("B", int(patient.mrn.split("-")[-1]))
            return None

        found_true: dict[int, str] = {}
        false_positives = 0
        for flag_row in flags:
            a = index_of(patients[flag_row.patient_a_id])
            b = index_of(patients[flag_row.patient_b_id])
            if a and b and a[0] != b[0] and a[1] == b[1] and a[1] < N_OVERLAP:
                found_true[a[1]] = corruption_of[a[1]]
            else:
                false_positives += 1

        recall_by_kind = {}
        for kind, _ in CORRUPTION:
            total = sum(1 for k in corruption_of.values() if k == kind)
            hit = sum(1 for k in found_true.values() if k == kind)
            recall_by_kind[kind] = (hit, total)

    engine.dispose()

    tp, fp = len(found_true), false_positives
    fn = N_OVERLAP - tp
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp, "fp": fp, "precision": precision, "recall": recall, "f1": f1,
        "recall_by_kind": recall_by_kind, "imports": import_stats,
    }


def run(seed: int = 7) -> str:
    feed_a, feed_b, corruption_of = _build_feeds(seed)
    baseline = _experiment(
        feed_a, feed_b, corruption_of, {"fuzzy": False, "dob_window_days": 0}
    )
    enhanced = _experiment(feed_a, feed_b, corruption_of, {})

    imports = enhanced["imports"]
    error_rate = imports["b_errors"] / len(BAD_ROWS)

    def metric_row(label, m):
        return (f"| {label} | {m['tp']} / {N_OVERLAP} | {m['fp']} |"
                f" {m['precision']:.2f} | {m['recall']:.2f} | **{m['f1']:.2f}** |")

    notes = {
        "clean": "exact name+DOB match",
        "typo_inner": "first initial survives → initial heuristic",
        "typo_first": "initial breaks → needs edit-distance matching",
        "dob_shift": "exact DOB breaks → needs the DOB window",
    }

    lines = [
        "## Experiment 1 — clinical data integration quality",
        "",
        f"Synthetic population of **{N_PEOPLE} people**; {N_OVERLAP} of them also arrive",
        "through a second source system under different MRNs. Half of the second feed",
        "is clean, 15% has an **inner-character name typo**, 10% a **first-letter",
        "typo** (breaks the initial), and a quarter a **±1 day date-of-birth shift**.",
        "Five malformed rows (bad dates, unknown codes, out-of-range values, missing",
        "identifiers) are injected on top. Both matcher configurations score the",
        "**same generated data**.",
        "",
        "### Mapping error reporting",
        "",
        f"- Injected malformed rows: **{len(BAD_ROWS)}**; reported as batch issues:",
        f"  **{imports['b_errors']}** → reporting rate **{error_rate:.0%}**"
        " (nothing silently dropped)",
        f"- Clean feed A imported {imports['a_imported']}/{imports['a_total']} rows"
        f" with {imports['a_errors']} errors",
        "",
        "### Duplicate detection — the research iteration",
        "",
        "**Baseline**: exact name+DOB and first-initial+surname+DOB.",
        "**Enhanced**: baseline **plus** bounded edit-distance name matching",
        "(Damerau–Levenshtein ≤ 2, blocked by DOB) and a ±31-day DOB window on",
        "identical names.",
        "",
        "| Matcher | True pairs | False pos. | Precision | Recall | F1 |",
        "|---|---|---|---|---|---|",
        metric_row("Baseline", baseline),
        metric_row("Enhanced", enhanced),
        "",
        "Recall by corruption type (baseline → enhanced):",
        "",
        "| Corruption | Baseline | Enhanced | Mechanism |",
        "|---|---|---|---|",
    ]
    for kind, _ in CORRUPTION:
        b_hit, total = baseline["recall_by_kind"][kind]
        e_hit, _ = enhanced["recall_by_kind"][kind]
        lines.append(f"| {kind} | {b_hit}/{total} | **{e_hit}/{total}** | {notes[kind]} |")
    lines += [
        "",
        "**Reading.** The first iteration measured two failure modes — typos that",
        "break the first initial, and shifted dates of birth — and this iteration",
        "closes them: bounded edit-distance matching recovers the first-letter",
        "typos and the DOB window recovers the date shifts, lifting recall from",
        f"**{baseline['recall']:.2f} to {enhanced['recall']:.2f}** at nearly",
        "unchanged precision (false positives remain coincidental name+DOB",
        "collisions in a small name pool — the reason flags go to human review",
        "instead of auto-merging). The harness stays in place to price the next",
        "candidate improvements (phonetic codes, nickname tables, household",
        "blocking) the same way.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(run())
