"""CLI entry point for the daily ClinicalTrials.gov sync job.

Invoked locally with `uv run python -m app.scripts.sync_trials`, and by the
`.github/workflows/sync-trials.yml` scheduled workflow in CI.
"""

import logging
import sys

from app.core.config import settings
from app.infrastructure.ctgov_client import ClinicalTrialsGovClient
from app.infrastructure.db import SessionLocal
from app.services.trial_sync_service import sync_clinical_trials

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    client = ClinicalTrialsGovClient(
        base_url=settings.ctgov_base_url,
        page_size=settings.ctgov_page_size,
    )

    with SessionLocal() as db:
        try:
            result = sync_clinical_trials(
                db, client, condition=settings.ctgov_condition_query
            )
        except Exception:
            logger.exception("Clinical trial sync failed")
            return 1

    logger.info(
        "Sync complete: created=%d updated=%d change_events=%d",
        result.created,
        result.updated,
        len(result.events),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
