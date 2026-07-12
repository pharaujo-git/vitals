"""Regenerate docs/EVALUATION.md from both experiments.

Usage: .venv/bin/python -m evaluation.run
"""

from pathlib import Path

from evaluation import integration_eval, risk_eval

HEADER = """# Vitals — Research Evaluation

Two experiments back the project's research angles, both fully reproducible
(`python -m evaluation.run`, fixed seeds, synthetic data only). The first
measures the **clinical data integration** pipeline end-to-end through the
production ingestion and duplicate-detection code; the second benchmarks the
**explainable risk rules** against a fitted logistic regression on data with
a known generative process.
"""


def main() -> None:
    sections = [HEADER, integration_eval.run(), "", risk_eval.run(), ""]
    target = Path(__file__).resolve().parents[2] / "docs" / "EVALUATION.md"
    target.write_text("\n".join(sections))
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
