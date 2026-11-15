# Queue submission

FastAPI saves the customer event and pending run in PostgreSQL. After that transaction commits, the route calls `enqueue_run(run_id)` from `src/support_engine/messaging.py`.

The helper creates an RQ job in the `support` queue. RQ stores the function reference and the run ID in Redis. The full customer event stays in PostgreSQL. Job arguments use JSON serialization.

```text
Verify and validate → save event + pending run → commit → enqueue run ID → HTTP 202
```

The job ID is `run-<run UUID>`. RQ's `unique=True` option prevents another job with that ID while the job exists. A matching retry returns that queued job ID. The helper checks the existing job's state and arguments before reporting success. This prevents duplicate queue entries at this step. It does not promise exactly-once execution.

## Response

A successful request returns HTTP 202:

```json
{
  "event_id": "demo_...",
  "status": "queued",
  "run_id": "...",
  "run_status": "pending",
  "job_id": "run-..."
}
```

`queued` describes submission. `pending` remains the saved run status until a worker starts. A run that is already beyond `pending` is not submitted again; a matching event then receives HTTP 200 with its saved receipt.

The simulator prints the queue receipt and stops. No worker container starts. The reserved `jobs.process_run` function raises `NotImplementedError` if someone starts a worker early. Implement worker execution in the next learning step before consuming the queue.

## Failure and manual retry

The PostgreSQL commit and Redis write are separate operations. A process can stop between them. A Redis timeout can also occur after the job was stored but before its acknowledgement reached FastAPI.

On a queue error, FastAPI returns HTTP 503 with the saved event ID, run ID, and `pending` status under `detail`. Submission is unconfirmed. The committed records remain in PostgreSQL. There is no automatic dispatcher or recovery scan.

After Redis recovers, resend the original event ID and content with a fresh signature timestamp. Matching input reuses the existing run and stable job ID. Running the normal simulator again creates a new event, so it is not a retry of the previous event.

For the current local demonstration, an operator with Docker access can also retry the helper directly. Replace the placeholder with a saved pending run UUID:

```bash
docker compose exec api python -c 'from support_engine.messaging import enqueue_run; print(enqueue_run("PASTE_SAVED_RUN_UUID"))'
```

This command only submits the ID. It does not validate the database record or execute the work. The HTTP retry remains the path that checks the original event against saved input.

A matching queued job is reused after an uncertain acknowledgement. If an existing job is failed, finished, or otherwise not queued, the helper reports an error instead of claiming it was queued again. Worker retry rules remain a later step.

## Run and inspect

```bash
docker compose up --build -d --wait
docker compose run --rm simulator
docker compose exec redis redis-cli LLEN rq:queue:support
docker compose exec redis redis-cli LRANGE rq:queue:support 0 -1
```

The last two commands show the queued job count and IDs. Jobs remain queued because no worker is running. The `queue-data` volume preserves Redis's append-only file. PostgreSQL remains the source of saved input and run state. Run status alone does not prove that a job is still present in Redis.

The current Redis role is RQ scheduling. Pub/Sub notices and SSE server delivery remain later steps, using this same Redis deployment.

Tests use random queue names and remove only their own jobs. They do not flush shared Redis or delete demonstration records.

Reference: [RQ job submission and uniqueness](https://python-rq.org/docs/).
