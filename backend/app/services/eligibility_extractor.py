"""Zero-cost, deterministic eligibility extraction for the MVP."""

import re
from abc import ABC, abstractmethod

from app.domain.eligibility import StructuredEligibility

_AGE_RANGE_PATTERNS = (
    re.compile(
        r"age\s*(?:>=|at least)\s*(?P<min>\d{1,3}).{0,30}?"
        r"(?:<=|at most)\s*(?P<max>\d{1,3})",
        re.IGNORECASE,
    ),
    re.compile(
        r"between\s+(?P<min>\d{1,3})\s+and\s+(?P<max>\d{1,3})\s+years",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?P<min>\d{1,3})\s*(?:years?)?\s*(?:to|-)\s*"
        r"(?P<max>\d{1,3})\s+years(?:\s+of\s+age)?",
        re.IGNORECASE,
    ),
)
_MIN_AGE_PATTERNS = (
    re.compile(
        r"age\s*(?:>=|at least)\s*(?P<min>\d{1,3})\s*(?:years?(?:\s+of\s+age)?)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:>=|at least)\s*(?P<min>\d{1,3})\s+years(?:\s+of\s+age)?",
        re.IGNORECASE,
    ),
)
_MAX_AGE_PATTERNS = (
    re.compile(
        r"age\s*(?:<=|at most)\s*(?P<max>\d{1,3})\s*(?:years?(?:\s+of\s+age)?)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:<=|at most)\s*(?P<max>\d{1,3})\s+years(?:\s+of\s+age)?",
        re.IGNORECASE,
    ),
)
_ECOG_PATTERN = re.compile(
    r"ECOG(?:\s+performance\s+status)?\s*(?:of|must be|:)?\s*([0-5](?:\s*(?:or|,|-)\s*[0-5])*)",
    re.IGNORECASE,
)
_PRIOR_TREATMENT_PATTERN = re.compile(
    r"prior\s+(?:treatment|therapy)\s+with\s+([A-Za-z0-9-]+)",
    re.IGNORECASE,
)


class EligibilityExtractor(ABC):
    """Converts free-text criteria into a replaceable structured contract."""

    @abstractmethod
    def extract(self, raw_eligibility_text: str) -> StructuredEligibility:
        """Return every criterion that can be extracted without raising."""


class RuleBasedEligibilityExtractor(EligibilityExtractor):
    """Regex/keyword extractor used by the zero-LLM MVP."""

    _FIELD_COUNT = 6

    def extract(self, raw_eligibility_text: str) -> StructuredEligibility:
        """Never raise: a single bad trial must not abort the daily sync."""
        try:
            return self._extract(raw_eligibility_text)
        except Exception:
            return self._empty_result()

    def _extract(self, raw_eligibility_text: str) -> StructuredEligibility:
        text = raw_eligibility_text.strip()
        if not text:
            return self._empty_result()

        age_min, age_max = _extract_age_range(text)
        diagnosis = _extract_diagnosis(text)
        prior_treatments = _extract_prior_treatments(text)
        ecog = _extract_ecog(text)
        biomarkers = _extract_biomarkers(text)
        brain_metastasis = _extract_brain_metastasis_policy(text)

        extracted_fields = sum(
            (
                age_min is not None or age_max is not None,
                diagnosis is not None,
                bool(prior_treatments),
                bool(ecog),
                bool(biomarkers),
                brain_metastasis is not None,
            )
        )

        return StructuredEligibility(
            age_min=age_min,
            age_max=age_max,
            diagnosis=diagnosis,
            prior_treatments=prior_treatments,
            ecog=ecog,
            biomarkers=biomarkers,
            brain_metastasis=brain_metastasis,
            extraction_confidence=round(extracted_fields / self._FIELD_COUNT, 2),
            extraction_method="rule",
        )

    @staticmethod
    def _empty_result() -> StructuredEligibility:
        return StructuredEligibility(
            extraction_confidence=0.0,
            extraction_method="rule",
        )


def _normalize_age(value: int | None) -> int | None:
    """Drop impossible ages (e.g. calendar-year false positives like 170)."""
    if value is None or value < 0 or value > 120:
        return None
    return value


def _extract_age_range(text: str) -> tuple[int | None, int | None]:
    for pattern in _AGE_RANGE_PATTERNS:
        if match := pattern.search(text):
            age_min = _normalize_age(int(match.group("min")))
            age_max = _normalize_age(int(match.group("max")))
            if age_min is not None and age_max is not None and age_min > age_max:
                return None, None
            return age_min, age_max

    minimum = _first_match(_MIN_AGE_PATTERNS, text)
    maximum = _first_match(_MAX_AGE_PATTERNS, text)
    age_min = _normalize_age(int(minimum.group("min")) if minimum else None)
    age_max = _normalize_age(int(maximum.group("max")) if maximum else None)
    if age_min is not None and age_max is not None and age_min > age_max:
        return None, None
    return age_min, age_max


def _first_match(patterns: tuple[re.Pattern[str], ...], text: str) -> re.Match[str] | None:
    for pattern in patterns:
        if match := pattern.search(text):
            return match
    return None


def _extract_diagnosis(text: str) -> str | None:
    if re.search(r"HER2(?:-positive|\+).{0,30}breast cancer", text, re.IGNORECASE):
        return "HER2-positive breast cancer"
    if re.search(r"breast cancer.{0,30}HER2(?:-positive|\+)", text, re.IGNORECASE):
        return "HER2-positive breast cancer"
    return None


def _extract_prior_treatments(text: str) -> list[str]:
    return list(
        dict.fromkeys(match.group(1).lower() for match in _PRIOR_TREATMENT_PATTERN.finditer(text))
    )


def _extract_ecog(text: str) -> list[int]:
    match = _ECOG_PATTERN.search(text)
    if not match:
        return []
    return sorted({int(value) for value in re.findall(r"[0-5]", match.group(1))})


def _extract_biomarkers(text: str) -> list[str]:
    biomarkers: list[str] = []
    patterns = (
        (r"HER2(?:-positive|\+)", "HER2-positive"),
        (r"(?:ER|estrogen receptor)(?:-positive|\+)", "ER-positive"),
        (r"(?:PR|progesterone receptor)(?:-positive|\+)", "PR-positive"),
    )
    for pattern, label in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            biomarkers.append(label)
    return biomarkers


def _extract_brain_metastasis_policy(text: str) -> bool | None:
    if re.search(
        r"(?:treated\s+and\s+stable|treated,\s*stable)\s+brain metastas",
        text,
        re.IGNORECASE,
    ):
        return True
    if re.search(
        r"(?:active|untreated)(?:\s+or\s+(?:active|untreated))?\s+brain metastas",
        text,
        re.IGNORECASE,
    ):
        return False
    return None
