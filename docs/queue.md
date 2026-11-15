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

The simulator prints the queue receipt and stops. A separate worker container consumes the queued jobs. `jobs.process_run` now implements the first worker operation. It claims a `pending` run with a conditional database update and commits `running`. It then loads the saved event, logs its type, and commits `completed`. Here, `completed` means that this test operation finished. It does not mean that a customer request was resolved.

The function skips runs whose status is not `pending`. It rejects an invalid UUID or a missing run. If the operation fails, it rolls back that transaction, saves `failed` in a new transaction, and raises the exception for RQ. If the process stops after the claim commits, the run can remain `running`. If the failure status cannot be saved, the run can also remain `running`. Recovery remains manual. No automatic retries are configured.

The `worker` service runs `python -m support_engine.worker`. It uses the same application image and queue settings as the API. Both queue submission and consumption use `JSONSerializer`. The worker uses a separate Redis connection. RQ sets its read timeout to exceed the blocking queue wait. Logs go to the container output.

The worker waits for Redis readiness and successful database migrations. One worker processes one job at a time. RQ starts a child process to execute each job. Compose allows 100 seconds for a graceful stop; the current job timeout is 90 seconds. A forced stop can still leave a run at `running`. The service restarts after a process exit, but failed jobs are not automatically retried.

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
docker compose up --build -d --wait api worker
docker compose run --rm simulator
docker compose logs --tail=50 worker
docker compose exec redis redis-cli LLEN rq:queue:support
docker compose exec redis redis-cli LRANGE rq:queue:support 0 -1
```

The last two commands show the queued job count and IDs. The worker can consume jobs before you inspect the queue. An empty queue alone does not prove success. Check the worker logs and the saved run status. The `queue-data` volume preserves Redis's append-only file. PostgreSQL remains the source of saved input and run state. Run status alone does not prove that a job is still present in Redis.

To stop or start the worker separately:

```bash
docker compose stop worker
docker compose up -d --wait worker
```

Starting the worker also consumes existing queued jobs. To process an isolated queue once, set `RQ_QUEUE` and run `python -m support_engine.worker --burst` in a one-off worker container. Burst mode exits when the queue is empty. Tests use this mode in a separate process.

The current Redis role is RQ scheduling. Pub/Sub notices and SSE server delivery remain later steps, using this same Redis deployment.

Tests use random queue names and remove only their own jobs. They do not flush shared Redis or delete demonstration records.

Reference: [RQ job submission and uniqueness](https://python-rq.org/docs/).
