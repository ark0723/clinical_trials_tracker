from app.domain.eligibility import StructuredEligibility
from app.services.eligibility_extractor import RuleBasedEligibilityExtractor
from app.services.extractor_eval import BenchmarkExample, evaluate_extractor


def test_evaluate_extractor_reports_f1_on_tiny_gold_set():
    gold = StructuredEligibility(
        age_min=18,
        age_max=75,
        diagnosis="HER2-positive breast cancer",
        biomarkers=["HER2-positive"],
        extraction_confidence=1.0,
        extraction_method="rule",
    )
    benchmark = [
        BenchmarkExample(
            nct_id="NCT-GOLD-1",
            raw_eligibility_text=(
                "Inclusion Criteria:\n"
                "- Age >= 18 and <= 75\n"
                "- HER2-positive breast cancer\n"
            ),
            gold=gold,
        )
    ]

    report = evaluate_extractor(RuleBasedEligibilityExtractor(), benchmark)

    assert report.sample_size == 1
    assert 0.0 <= report.precision <= 1.0
    assert 0.0 <= report.recall <= 1.0
    assert 0.0 <= report.f1 <= 1.0
