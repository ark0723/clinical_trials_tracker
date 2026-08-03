"""Deterministic plain-English eligibility summaries for the zero-LLM MVP."""

from app.domain.eligibility import StructuredEligibility


class RuleBasedEligibilitySummarizer:
    """Builds a short summary only from facts the extractor identified."""

    def summarize(self, eligibility: StructuredEligibility) -> str | None:
        sentences: list[str] = []

        if eligibility.diagnosis and eligibility.age_min is not None:
            subject = _age_and_diagnosis_sentence(eligibility)
            sentences.append(subject)
        elif eligibility.diagnosis:
            sentences.append(f"This study is for people with {eligibility.diagnosis}.")
        elif eligibility.age_min is not None or eligibility.age_max is not None:
            sentences.append(_age_only_sentence(eligibility))

        if eligibility.ecog:
            values = " or ".join(str(value) for value in eligibility.ecog)
            sentences.append(f"Participants must have an ECOG performance status of {values}.")

        if eligibility.prior_treatments:
            treatments = ", ".join(eligibility.prior_treatments)
            sentences.append(f"Prior treatment with {treatments} is required.")

        if eligibility.brain_metastasis is False:
            sentences.append(
                "People with active or untreated brain metastases are not eligible."
            )
        elif eligibility.brain_metastasis is True:
            sentences.append("Treated and stable brain metastases may be allowed.")

        return " ".join(sentences) or None


def _age_and_diagnosis_sentence(eligibility: StructuredEligibility) -> str:
    if eligibility.age_max is not None:
        return (
            f"This study is for adults ages {eligibility.age_min} to "
            f"{eligibility.age_max} with {eligibility.diagnosis}."
        )
    return (
        f"This study is for adults age {eligibility.age_min} or older "
        f"with {eligibility.diagnosis}."
    )


def _age_only_sentence(eligibility: StructuredEligibility) -> str:
    if eligibility.age_min is not None and eligibility.age_max is not None:
        return f"This study is for adults ages {eligibility.age_min} to {eligibility.age_max}."
    if eligibility.age_min is not None:
        return f"This study is for adults age {eligibility.age_min} or older."
    return f"This study is for adults age {eligibility.age_max} or younger."
