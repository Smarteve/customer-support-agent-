"""Execute the first worker milestone without customer-facing actions."""

import logging
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from support_engine.database import Event, Run, make_engine

logger = logging.getLogger(__name__)


def process_run(run_id: str) -> None:
    """Claim a pending run and log its event type. Recovery remains manual."""
    saved_id = UUID(run_id)
    engine = make_engine()
    try:
        with Session(engine) as session:
            with session.begin():
                claimed = session.scalar(
                    update(Run)
                    .where(Run.id == saved_id, Run.status == "pending")
                    .values(status="running")
                    .returning(Run.event_id)
                )
                if claimed is None:
                    if session.get(Run, saved_id) is None:
                        raise ValueError(f"Run {saved_id} does not exist")
                    logger.info("Skipping run %s: status is not pending", saved_id)
                    return
            # The claim commits before work starts. A crash can leave the run running.
            try:
                with session.begin():
                    event = session.scalar(select(Event).where(Event.id == claimed))
                    if event is None:
                        raise ValueError(f"Event for run {saved_id} does not exist")
                    logger.info("Processing run %s: event type %s", saved_id, event.event_type)
                    session.execute(
                        update(Run).where(Run.id == saved_id).values(status="completed")
                    )
            except Exception:
                # The failed work transaction has rolled back before this transaction.
                with session.begin():
                    session.execute(update(Run).where(Run.id == saved_id).values(status="failed"))
                raise
    finally:
        engine.dispose()
