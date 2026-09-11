# Reservation delivery preparation

This change is a deployment candidate, not a live storage migration.

## Required configuration before deployment

Set `RESERVATION_DB_PATH` in Streamlit secrets or the environment to an absolute
SQLite filename on a persistent private volume. Its parent directory must already
exist, be writable by the application, and be accessible only to its operator.
Keep the database and its backups outside any public/static directory. Use one
application instance with a local persistent volume; this is not a shared network
SQLite or multi-instance deployment design.

For a local demo only:

```bash
mkdir -m 700 -p "$PWD/private-data"
export RESERVATION_DB_PATH="$PWD/private-data/reservations.sqlite3"
streamlit run tools/lead_qualifier/app.py
```

Do not use the local-demo directory as proof of production durability. An
ephemeral Streamlit host can discard local files on restart or redeployment.
Before deploying, provide a persistent volume or implement an external database
adapter. Missing storage deliberately prevents notification and success messages.
The code cannot verify a hosting provider's volume persistence itself.

## Delivery and staff review

Requests are committed before Telegram is called. The states are:

- `sent`: the Telegram HTTP call completed successfully.
- `needs_attention`: notification configuration was missing.
- `unknown`: notification failed, timed out, or the process stopped around the
  send. Telegram may already contain the message.

There is no background retry worker. Staff must inspect unsent/unknown requests
and reconcile them with Telegram before contacting a guest. A saved request does
not confirm table availability. The guest is shown this distinction.

From a private operator terminal with the SQLite CLI installed:

```bash
sqlite3 -readonly "$RESERVATION_DB_PATH" \
  "SELECT request_id,created_at,status,payload FROM reservations WHERE status != 'sent' ORDER BY created_at;"
```

This output contains customer contact details; do not paste it into public issues
or logs. Arrange an operator review schedule and private backups before accepting
real requests. Test restoration to a separate database. Define retention with the
venue instead of retaining customer data indefinitely.

Repeated submission of the same data in one Streamlit browser session reuses the
request ID and does not send again. A new browser session can create a new request;
cross-session duplicate detection and spam controls are not implemented here.
The database's primary key also prevents concurrent attempts for the same ID.

## Verification

```bash
python -m pytest tests/lead_qualifier/test_app.py tests/lead_qualifier/test_rag_assistant.py tests/lead_qualifier/test_reservations.py -q
```

Tests use temporary databases, fake credentials, and mocked notification calls.
They cover save-before-send, concurrent duplicate submission, timeout/retry,
missing storage, conflicting request IDs, and kitchen/breakfast hours.
No real guest requests or external messages are sent by these tests.
