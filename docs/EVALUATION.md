# Vitals — Research Evaluation

Two experiments back the project's research angles, both fully reproducible
(`python -m evaluation.run`, fixed seeds, synthetic data only). The first
measures the **clinical data integration** pipeline end-to-end through the
production ingestion and duplicate-detection code; the second benchmarks the
**explainable risk rules** against a fitted logistic regression on data with
a known generative process.

## Experiment 1 — clinical data integration quality

Synthetic population of **200 people**; 120 of them also arrive
through a second source system under different MRNs. Half of the second feed
is clean, 15% has an **inner-character name typo**, 10% a **first-letter
typo** (breaks the initial), and a quarter a **±1 day date-of-birth shift**.
Five malformed rows (bad dates, unknown codes, out-of-range values, missing
identifiers) are injected on top.

### Mapping error reporting

- Injected malformed rows: **5**
- Rows reported as batch issues: **5** → reporting rate **100%** (nothing silently dropped)
- Clean feed A imported 200/200 rows with 0 errors

### Duplicate detection (name + DOB heuristics)

| Metric | Value |
|---|---|
| True pairs found | 81 / 120 |
| False positives | 1 |
| Precision | **0.99** |
| Recall | **0.68** |
| F1 | **0.80** |

Recall by corruption type:

| Corruption | Found | Notes |
|---|---|---|
| clean | 69/69 | exact name+DOB match |
| typo_inner | 12/12 | first initial survives, so the initial+surname+DOB heuristic catches these |
| typo_first | 0/17 | the initial breaks — missed by both heuristics |
| dob_shift | 0/22 | missed by design — the heuristics require an exact DOB |

**Reading.** Exact and inner-typo duplicates are handled by MRN upsert
plus the two name+DOB heuristics; false positives come from coincidental
name+DOB collisions in a small name pool, which is why flags go to human
review instead of auto-merging. The two failure modes measured here —
typos that break the first initial, and DOB shifts — motivate the obvious
next step for the research agenda: phonetic name codes (Soundex/Metaphone)
and windowed DOB blocking, then re-running this same harness to quantify
the gain.

## Experiment 2 — explainable rules vs logistic regression

Synthetic cohort of **4000 patients** with a known generative outcome
(a latent deterioration risk over the same physiology the rule engine
watches, plus noise for unmeasured factors). Base rate:
**15%** positive. 35% held-out test set.

| Model | AUC | Precision | Recall | F1 |
|---|---|---|---|---|
| Rule-based score (threshold ≥ 3) | 0.781 | 0.27 | 0.81 | 0.41 |
| Logistic regression (8 features) | 0.814 | 0.62 | 0.25 | 0.36 |

Fitted coefficients (standardized features, magnitude order):

| Feature | Coefficient |
|---|---|
| age | +0.798 |
| glucose | +0.488 |
| hba1c | +0.369 |
| bp_systolic | +0.335 |
| spo2 | -0.226 |
| bmi | +0.202 |
| bp_diastolic | +0.166 |
| heart_rate | -0.017 |

**Reading.** The fitted model recovers the generative structure (its
coefficient ordering mirrors the latent weights) and buys a few AUC
points over the hand-written rules — the price of the rules' step
thresholds. What the rules buy back is the explanation: every flag in
the product lists the exact thresholds crossed with measured values,
while the regression's evidence is a weighted sum. For the
lightweight-decision-support research angle, this quantifies the
accuracy/explainability trade the dashboard makes, and gives the exact
harness to evaluate richer explainable models (scorecards, shallow
trees) against both baselines.
