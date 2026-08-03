"""Maps raw ClinicalTrials.gov API v2 study JSON to our ClinicalTrial domain model."""

from datetime import UTC, datetime
from typing import Any

from app.domain.clinical_trial import ClinicalTrial, TrialLocation, TrialPhase, TrialStatus


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    # ClinicalTrials.gov dates are "YYYY-MM-DD" or "YYYY-MM"; normalize to a full date.
    parts = date_str.split("-")
    year = int(parts[0])
    month = int(parts[1]) if len(parts) > 1 else 1
    day = int(parts[2]) if len(parts) > 2 else 1
    return datetime(year, month, day, tzinfo=UTC)


def _map_phase(phases: list[str]) -> TrialPhase:
    """ClinicalTrials.gov sends phases like "PHASE2"/"NA"; our enum uses "PHASE_2".

    For combination trials (e.g. ["PHASE1", "PHASE2"]) we take the highest phase.
    """
    if not phases:
        return TrialPhase.NOT_APPLICABLE

    normalized = [phase.replace("PHASE", "PHASE_") for phase in phases]
    for candidate in sorted(normalized, reverse=True):
        try:
            return TrialPhase(candidate)
        except ValueError:
            continue
    return TrialPhase.NOT_APPLICABLE


def _map_status(raw_status: str | None) -> TrialStatus:
    """Falls back to UNKNOWN for any value ClinicalTrials.gov adds in the
    future that we haven't mapped yet, so one unrecognized trial doesn't
    abort the entire sync batch."""
    if raw_status is None:
        return TrialStatus.UNKNOWN
    try:
        return TrialStatus(raw_status)
    except ValueError:
        return TrialStatus.UNKNOWN


def _map_locations(raw_locations: list[dict[str, Any]]) -> list[TrialLocation]:
    locations = []
    for raw_location in raw_locations:
        geo_point = raw_location.get("geoPoint") or {}
        locations.append(
            TrialLocation(
                facility=raw_location.get("facility"),
                city=raw_location.get("city"),
                country=raw_location.get("country"),
                latitude=geo_point.get("lat"),
                longitude=geo_point.get("lon"),
            )
        )
    return locations


def map_study_to_trial(raw_study: dict[str, Any]) -> ClinicalTrial:
    protocol = raw_study.get("protocolSection", {})
    identification = protocol.get("identificationModule", {})
    status_module = protocol.get("statusModule", {})
    design_module = protocol.get("designModule", {})
    eligibility_module = protocol.get("eligibilityModule", {})
    contacts_locations_module = protocol.get("contactsLocationsModule", {})

    enrollment_info = design_module.get("enrollmentInfo") or {}
    last_updated = _parse_date(
        status_module.get("lastUpdatePostDateStruct", {}).get("date")
    ) or datetime.now(UTC)

    return ClinicalTrial(
        nct_id=identification["nctId"],
        title=identification.get("briefTitle", ""),
        phase=_map_phase(design_module.get("phases", [])),
        status=_map_status(status_module.get("overallStatus")),
        eligibility_criteria_raw=eligibility_module.get("eligibilityCriteria", ""),
        enrollment_count=enrollment_info.get("count"),
        has_results=raw_study.get("hasResults", False),
        locations=_map_locations(contacts_locations_module.get("locations") or []),
        last_updated=last_updated,
    )
