from app.domain.eligibility import StructuredEligibility
from app.services.eligibility_extractor import RuleBasedEligibilityExtractor


def test_extracts_core_eligibility_fields_from_common_clinical_language():
    raw_text = """
    Inclusion Criteria:
    - Age >= 18 and <= 75 years
    - Histologically confirmed HER2-positive breast cancer
    - ECOG performance status 0 or 1
    - Prior treatment with trastuzumab is required

    Exclusion Criteria:
    - Active or untreated brain metastases
    """

    result = RuleBasedEligibilityExtractor().extract(raw_text)

    assert result == StructuredEligibility(
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


def test_returns_partial_result_without_raising_for_unstructured_text():
    result = RuleBasedEligibilityExtractor().extract(
        "Patients should be suitable for the investigational treatment."
    )

    assert result.age_min is None
    assert result.age_max is None
    assert result.diagnosis is None
    assert result.prior_treatments == []
    assert result.ecog == []
    assert result.biomarkers == []
    assert result.brain_metastasis is None
    assert result.extraction_confidence == 0.0
    assert result.extraction_method == "rule"


def test_handles_empty_eligibility_text():
    result = RuleBasedEligibilityExtractor().extract("")

    assert result == StructuredEligibility(
        extraction_confidence=0.0,
        extraction_method="rule",
    )


def test_extracts_age_from_between_expression():
    result = RuleBasedEligibilityExtractor().extract(
        "Participants must be between 21 and 70 years of age."
    )

    assert result.age_min == 21
    assert result.age_max == 70


def test_allows_treated_stable_brain_metastases():
    result = RuleBasedEligibilityExtractor().extract(
        "Patients with treated and stable brain metastases are eligible."
    )

    assert result.brain_metastasis is True


def test_ignores_out_of_range_ages_instead_of_raising():
    """`\\d{1,3}` can latch onto the first three digits of a calendar year
    (e.g. '>= 1700' → 170). Discard impossible ages instead of crashing sync."""
    result = RuleBasedEligibilityExtractor().extract(
        "Age >= 1700 years. HER2-positive breast cancer."
    )

    assert result.age_min is None
    assert result.age_max is None
    assert result.diagnosis == "HER2-positive breast cancer"
    assert result.extraction_method == "rule"


def test_does_not_confuse_lab_values_or_vitals_with_age():
    """Blood pressure and lab thresholds also use >= N; must not become age_min."""
    result = RuleBasedEligibilityExtractor().extract(
        "Systolic blood pressure >=170 or diastolic >=110. "
        "ANC >= 1500/mm3. HER2-positive breast cancer."
    )

    assert result.age_min is None
    assert result.age_max is None
    assert result.diagnosis == "HER2-positive breast cancer"
