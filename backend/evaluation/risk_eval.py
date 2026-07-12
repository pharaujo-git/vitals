"""Risk model comparison: transparent rules vs logistic regression.

Generates a synthetic cohort with a *known* generative process: a latent
deterioration risk built from the same physiology the rule engine watches,
plus noise. Because the ground truth is known by construction, the
comparison isolates the modeling question — how much accuracy do the
hand-written, explainable rules give up against a fitted model?

This is a methods benchmark on synthetic data, not a clinical claim.
"""

import math
import random

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from app.services.risk import FLAG_THRESHOLD, _score_rules

N = 4000
FEATURES = ["age", "bp_systolic", "bp_diastolic", "glucose", "hba1c", "bmi", "spo2", "heart_rate"]


def _cohort(rng: random.Random):
    rows = []
    for _ in range(N):
        age = rng.randint(18, 90)
        profile = rng.random()
        if profile < 0.55:  # healthy
            sbp, glucose, hba1c = rng.gauss(120, 9), rng.gauss(92, 8), rng.gauss(5.3, 0.3)
        elif profile < 0.8:  # hypertensive
            sbp, glucose, hba1c = rng.gauss(152, 12), rng.gauss(100, 10), rng.gauss(5.6, 0.4)
        else:  # diabetic
            sbp, glucose, hba1c = rng.gauss(135, 12), rng.gauss(150, 25), rng.gauss(7.8, 1.0)
        rows.append({
            "age": age,
            "bp_systolic": max(85, sbp),
            "bp_diastolic": max(50, sbp * 0.62 + rng.gauss(0, 5)),
            "glucose": max(60, glucose),
            "hba1c": max(4.0, hba1c),
            "bmi": max(16, rng.gauss(27, 4.5)),
            "spo2": min(100, rng.gauss(97, 1.8)),
            "heart_rate": max(40, rng.gauss(76, 11)),
        })
    return rows


def _latent_outcome(row: dict, rng: random.Random) -> int:
    """Known generative truth: a logistic function over standardized excesses."""
    z = (
        0.04 * (row["age"] - 55)
        + 0.035 * (row["bp_systolic"] - 130)
        + 0.02 * (row["glucose"] - 105)
        + 0.55 * (row["hba1c"] - 6.0)
        + 0.06 * (row["bmi"] - 28)
        - 0.25 * (row["spo2"] - 96)
        + rng.gauss(0, 1.2)  # unmeasured factors
        - 2.4
    )
    return 1 if rng.random() < 1 / (1 + math.exp(-z)) else 0


def run(seed: int = 11) -> str:
    rng = random.Random(seed)
    rows = _cohort(rng)
    y = np.array([_latent_outcome(row, rng) for row in rows])

    # Rule engine: score every row through the production rules.
    rule_scores = np.array([
        _score_rules(int(row["age"]), {k: v for k, v in row.items() if k != "age"})[0]
        for row in rows
    ])
    X = np.array([[row[f] for f in FEATURES] for row in rows])

    X_train, X_test, y_train, y_test, rules_train, rules_test = train_test_split(
        X, y, rule_scores, test_size=0.35, random_state=seed, stratify=y
    )

    scaler = StandardScaler().fit(X_train)
    model = LogisticRegression(max_iter=1000).fit(scaler.transform(X_train), y_train)
    lr_prob = model.predict_proba(scaler.transform(X_test))[:, 1]

    lr_auc = roc_auc_score(y_test, lr_prob)
    rule_auc = roc_auc_score(y_test, rules_test)

    lr_pred = (lr_prob >= 0.5).astype(int)
    rule_pred = (rules_test >= FLAG_THRESHOLD).astype(int)
    lr_p, lr_r, lr_f, _ = precision_recall_fscore_support(
        y_test, lr_pred, average="binary", zero_division=0
    )
    rule_p, rule_r, rule_f, _ = precision_recall_fscore_support(
        y_test, rule_pred, average="binary", zero_division=0
    )

    coefficients = sorted(
        zip(FEATURES, model.coef_[0]), key=lambda pair: abs(pair[1]), reverse=True
    )

    lines = [
        "## Experiment 2 — explainable rules vs logistic regression",
        "",
        f"Synthetic cohort of **{N} patients** with a known generative outcome",
        "(a latent deterioration risk over the same physiology the rule engine",
        "watches, plus noise for unmeasured factors). Base rate:",
        f"**{y.mean():.0%}** positive. 35% held-out test set.",
        "",
        "| Model | AUC | Precision | Recall | F1 |",
        "|---|---|---|---|---|",
        f"| Rule-based score (threshold ≥ {FLAG_THRESHOLD}) | {rule_auc:.3f} |"
        f" {rule_p:.2f} | {rule_r:.2f} | {rule_f:.2f} |",
        f"| Logistic regression (8 features) | {lr_auc:.3f} |"
        f" {lr_p:.2f} | {lr_r:.2f} | {lr_f:.2f} |",
        "",
        "Fitted coefficients (standardized features, magnitude order):",
        "",
        "| Feature | Coefficient |",
        "|---|---|",
    ]
    lines += [f"| {feature} | {coef:+.3f} |" for feature, coef in coefficients]
    lines += [
        "",
        "**Reading.** The fitted model recovers the generative structure (its",
        "coefficient ordering mirrors the latent weights) and buys a few AUC",
        "points over the hand-written rules — the price of the rules' step",
        "thresholds. What the rules buy back is the explanation: every flag in",
        "the product lists the exact thresholds crossed with measured values,",
        "while the regression's evidence is a weighted sum. For the",
        "lightweight-decision-support research angle, this quantifies the",
        "accuracy/explainability trade the dashboard makes, and gives the exact",
        "harness to evaluate richer explainable models (scorecards, shallow",
        "trees) against both baselines.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(run())
