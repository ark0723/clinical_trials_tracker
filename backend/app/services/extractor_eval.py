"""Minimal eligibility-extractor evaluation harness (gold-set based).

Metric definitions and gold labels are owned by the researcher; this module
only computes field-level Precision/Recall/F1 against provided examples.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.eligibility import StructuredEligibility
from app.services.eligibility_extractor import EligibilityExtractor


@dataclass(frozen=True)
class BenchmarkExample:
    nct_id: str
    raw_eligibility_text: str
    gold: StructuredEligibility


@dataclass(frozen=True)
class EvaluationReport:
    precision: float
    recall: float
    f1: float
    sample_size: int
    evaluated_at: datetime


_COMPARABLE_FIELDS = (
    "age_min",
    "age_max",
    "diagnosis",
    "brain_metastasis",
)


def evaluate_extractor(
    extractor: EligibilityExtractor,
    benchmark: list[BenchmarkExample],
) -> EvaluationReport:
    if not benchmark:
        raise ValueError("benchmark must contain at least one example")

    true_positive = 0
    false_positive = 0
    false_negative = 0

    for example in benchmark:
        predicted = extractor.extract(example.raw_eligibility_text)
        for field in _COMPARABLE_FIELDS:
            gold_value = getattr(example.gold, field)
            pred_value = getattr(predicted, field)
            if gold_value is None and pred_value is None:
                continue
            if gold_value is None and pred_value is not None:
                false_positive += 1
            elif gold_value is not None and pred_value is None:
                false_negative += 1
            elif _values_match(gold_value, pred_value):
                true_positive += 1
            else:
                false_positive += 1
                false_negative += 1

        gold_markers = {m.lower() for m in example.gold.biomarkers}
        pred_markers = {m.lower() for m in predicted.biomarkers}
        true_positive += len(gold_markers & pred_markers)
        false_positive += len(pred_markers - gold_markers)
        false_negative += len(gold_markers - pred_markers)

    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive
        else 0.0
    )
    recall = (
        true_positive / (true_positive + false_negative)
        if true_positive + false_negative
        else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall) if precision + recall else 0.0
    )
    return EvaluationReport(
        precision=precision,
        recall=recall,
        f1=f1,
        sample_size=len(benchmark),
        evaluated_at=datetime.now(UTC),
    )


def _values_match(gold: object, pred: object) -> bool:
    if isinstance(gold, str) and isinstance(pred, str):
        return gold.lower() in pred.lower() or pred.lower() in gold.lower()
    return gold == pred
