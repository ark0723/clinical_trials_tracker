from app.domain.eligibility import StructuredEligibility
from app.services.eligibility_summarizer import RuleBasedEligibilitySummarizer


def test_builds_plain_english_summary_from_structured_criteria():
    eligibility = StructuredEligibility(
        age_min=18,
        age_max=75,
        diagnosis="HER2-positive breast cancer",
        prior_treatments=["trastuzumab"],
        ecog=[0, 1],
        biomarkers=["HER2-positive"],
        brain_metastasis=False,
        extraction_confidence=1.0,
        extraction_method="rule",
    )

    summary = RuleBasedEligibilitySummarizer().summarize(eligibility)

    assert summary == (
        "This study is for adults ages 18 to 75 with HER2-positive breast cancer. "
        "Participants must have an ECOG performance status of 0 or 1. "
        "Prior treatment with trastuzumab is required. "
        "People with active or untreated brain metastases are not eligible."
    )


def test_returns_none_when_no_criteria_were_extracted():
    eligibility = StructuredEligibility(
        extraction_confidence=0.0,
        extraction_method="rule",
    )

    assert RuleBasedEligibilitySummarizer().summarize(eligibility) is None
