# Important Code Snippets

This file collects a few small patterns that students often need during the exam.

## Read values from `.env` with `os.getenv`

Use `os.getenv` when a value must come from the environment or `.env` file.

```python
import os

API_BASE_URL = os.getenv("GARAGE_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
STUDENT_NAME = os.getenv("STUDENT_NAME", "Student")
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "7860"))
```

What this does:

- `os.getenv("GARAGE_API_BASE_URL", "http://127.0.0.1:8000")` reads the value from the environment.
- If the variable is missing, the second value is used as a fallback.
- `.rstrip("/")` removes a trailing slash so URL building stays clean.
- `int(...)` converts a string from the environment into a real number.

## Keep the backend URL in one constant

Read the backend URL once, then reuse it everywhere in the frontend.

```python
API_BASE_URL = os.getenv("GARAGE_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

response = httpx.get(f"{API_BASE_URL}/cars")
```

This avoids hardcoding `http://127.0.0.1:8000` in many places.

Important note:

- In this starter repository, the environment variable is named `GARAGE_API_BASE_URL`.
- It is still fine to keep the Python constant name as `API_BASE_URL`.
- If a future assignment uses `API_BASE_URL` directly in `.env`, the same pattern still works:

```python
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
```

## Read `STUDENT_NAME` safely

This pattern is useful when you want a clean fallback value:

```python
student_name = os.getenv("STUDENT_NAME", "Student").strip() or "Student"
```

Why this is useful:

- `os.getenv(..., "Student")` gives a default when the variable is missing.
- `.strip()` removes accidental spaces.
- `or "Student"` also protects against an empty string like `STUDENT_NAME=`.

## Seeding with explicit IDs

When you import starter data, you often set `id` values manually.

```python
session.add(
    Car(
        id=9001,
        license_plate="STUDENT-1",
        brand="Student",
        model="Demo",
        owner_name=student_name,
    )
)
session.flush()
```

This works, but it creates one common PostgreSQL problem:

- the table data may already contain high `id` values
- the PostgreSQL sequence counter may still be lower
- the next automatic insert can then fail with a duplicate key error

## Sync PostgreSQL sequences after seeding

If you seed rows with manual `id` values, update the PostgreSQL sequence after the seed has been written.

```python
from sqlalchemy import text


def _sync_postgres_sequences(session: Session):
    if engine.dialect.name != "postgresql":
        return

    for table_name in ("service_bays", "cars", "repairs", "charge_cycles", "battery_logs", "logs"):
        session.exec(
            text(
                "SELECT setval("
                "pg_get_serial_sequence(:table_name, 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {table_name}), 1), "
                "true)"
            ).bindparams(table_name=table_name)
        )
    session.commit()
```

What this fixes:

- PostgreSQL looks up the sequence behind each `id` column.
- `MAX(id)` finds the highest seeded ID already in the table.
- `setval(..., true)` moves the sequence to that value.
- The next automatic insert then continues at the correct next ID.

## Recommended seed order

A safe pattern is:

```python
with Session(engine) as session:
    # add seed data
    session.add(...)
    session.add(...)
    session.flush()

    # write everything to the database
    session.commit()

    # fix the sequence counters for future inserts
    _sync_postgres_sequences(session)
```

In this repository, the seed flow already finishes by calling `_sync_postgres_sequences(session)` after inserting the starter data.

## When to use `flush()`

`session.flush()` sends pending inserts to the database without fully finishing the transaction yet.

Use it when:

- you want generated IDs before the final commit
- you want to create related rows in the same transaction
- you want to check whether the data can be written before moving on

Use `session.commit()` when you want to permanently save the transaction.

## Practical rule of thumb

If a value may change between students, machines, or grading setups, read it from `.env` with `os.getenv`.

If you seed rows with manual IDs in PostgreSQL, sync the sequences before trusting future inserts without explicit IDs.