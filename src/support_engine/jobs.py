"""Reserved RQ job entry point. No worker is started at this learning milestone."""


def process_run(run_id: str) -> None:
    raise NotImplementedError("Worker execution is a later step. Keep jobs queued for now.")
