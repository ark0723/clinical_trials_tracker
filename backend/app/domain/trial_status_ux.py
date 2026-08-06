"""Plain-English explanations for ClinicalTrials.gov overallStatus labels.

Source of truth remains the official status string; this layer never replaces it.
"""

from __future__ import annotations

from app.domain.clinical_trial import TrialStatus

# Official CT.gov display labels (US English).
STATUS_LABELS: dict[TrialStatus, str] = {
    TrialStatus.RECRUITING: "Recruiting",
    TrialStatus.NOT_YET_RECRUITING: "Not yet recruiting",
    TrialStatus.ACTIVE_NOT_RECRUITING: "Active, not recruiting",
    TrialStatus.ENROLLING_BY_INVITATION: "Enrolling by invitation",
    TrialStatus.SUSPENDED: "Suspended",
    TrialStatus.COMPLETED: "Completed",
    TrialStatus.TERMINATED: "Terminated",
    TrialStatus.WITHDRAWN: "Withdrawn",
    TrialStatus.AVAILABLE: "Available",
    TrialStatus.NO_LONGER_AVAILABLE: "No longer available",
    TrialStatus.APPROVED_FOR_MARKETING: "Approved for marketing",
    TrialStatus.WITHHELD: "Withheld",
    TrialStatus.UNKNOWN: "Unknown",
}

STATUS_MEANINGS: dict[TrialStatus, str] = {
    TrialStatus.RECRUITING: "This trial is currently looking for participants.",
    TrialStatus.NOT_YET_RECRUITING: (
        "The study is registered but is not accepting participants yet."
    ),
    TrialStatus.ACTIVE_NOT_RECRUITING: (
        "The study is ongoing but is not currently enrolling new participants."
    ),
    TrialStatus.ENROLLING_BY_INVITATION: (
        "Participation is limited to people invited by the study team."
    ),
    TrialStatus.SUSPENDED: "Enrollment or study activity is temporarily paused.",
    TrialStatus.COMPLETED: (
        "The study has finished. Results may help explain why a treatment became "
        "standard care — this is not an open enrollment opportunity."
    ),
    TrialStatus.TERMINATED: "The study was stopped early and is not enrolling.",
    TrialStatus.WITHDRAWN: "The study was withdrawn before enrolling participants.",
    TrialStatus.AVAILABLE: "Expanded access to the intervention may be available.",
    TrialStatus.NO_LONGER_AVAILABLE: "Expanded access is no longer available.",
    TrialStatus.APPROVED_FOR_MARKETING: (
        "The intervention has been approved for marketing."
    ),
    TrialStatus.WITHHELD: "Status details are withheld on ClinicalTrials.gov.",
    TrialStatus.UNKNOWN: "Status could not be mapped from ClinicalTrials.gov.",
}

# Patient Mode default: join-now intent (excludes Enrolling by invitation).
PATIENT_DEFAULT_STATUSES: frozenset[TrialStatus] = frozenset(
    {
        TrialStatus.RECRUITING,
        TrialStatus.NOT_YET_RECRUITING,
    }
)

# Common filter chips for Patient Mode (original CT.gov labels).
PATIENT_FILTER_STATUSES: tuple[TrialStatus, ...] = (
    TrialStatus.RECRUITING,
    TrialStatus.NOT_YET_RECRUITING,
    TrialStatus.ACTIVE_NOT_RECRUITING,
    TrialStatus.ENROLLING_BY_INVITATION,
    TrialStatus.COMPLETED,
    TrialStatus.TERMINATED,
    TrialStatus.WITHDRAWN,
    TrialStatus.SUSPENDED,
)


def status_label(status: TrialStatus) -> str:
    return STATUS_LABELS.get(status, status.value.replace("_", " ").title())


def status_meaning(status: TrialStatus) -> str:
    return STATUS_MEANINGS.get(status, "See ClinicalTrials.gov for status details.")
