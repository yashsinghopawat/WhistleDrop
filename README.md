# WhistleDrop

Backend for an anonymous reporting system (GDG on Campus SRM recruitment task, Backend #1).

Anyone can send a report without an account. They get a case code and can use it later to check what
happened to the report. Moderators log in, review the reports and update their status. They cannot see
who sent a report, because that information is never saved.

Built with Python, FastAPI, PostgreSQL, SQLAlchemy 2.0, Pydantic v2, JWT and bcrypt.

## Setup

1. Install PostgreSQL and create two databases:
   ```sql
   CREATE DATABASE whistledrop;
   CREATE DATABASE whistledrop_test;
   ```
2. Create a virtual environment and install the packages:
   ```bash
   python -m venv venv
   venv\Scripts\activate          # Windows
   source venv/bin/activate       # Linux / Mac
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your database password, a secret key and a moderator invite code.
4. Start the server:
   ```bash
   python run.py
   ```
   If you start it with the `uvicorn` command instead, add `--no-access-log` (see "Anonymity" below).
   The tables are created automatically on startup.
5. Open http://127.0.0.1:8000/docs
6. Run the tests with `pytest`. They use `TEST_DATABASE_URL`, so your real data is not touched.

## Folder structure

```
app/
  main.py          app creation + routers
  core/            config.py (settings from .env), security.py (passwords, JWT, case codes)
  database/        engine, session, base class
  models/          tables: User, Report, StatusUpdate, plus the enums
  schemas/         Pydantic request/response classes
  repositories/    database queries
  services/        business rules
  api/             dependencies.py (current user) and routes/
tests/
screenshots/
```

Flow of a request: route -> schema validation -> auth -> service -> repository -> SQLAlchemy -> PostgreSQL.

## Trying it in Swagger

1. `POST /reports` and copy the `case_code`
2. `POST /reports/track` with that code to see the status
3. `POST /auth/register` with the invite code from your `.env`
4. `POST /auth/login`, copy the token, press **Authorize** and paste it
5. Use the `/moderation/reports` endpoints
6. Track the report again to see the moderator's update

## Endpoints

| Method | Endpoint | Login needed | What it does |
|---|---|---|---|
| POST | `/reports` | no | Submit a report, returns the case code |
| POST | `/reports/track` | no | Check a report with its case code |
| POST | `/auth/register` | no (invite code) | Create a moderator |
| POST | `/auth/login` | no | Get a JWT token |
| GET | `/users/me` | yes | Logged-in moderator |
| GET | `/moderation/reports` | yes | List reports. Filters: `category`, `status`, `search`, `skip`, `limit` |
| GET | `/moderation/reports/stats` | yes | Counts per status and category |
| GET | `/moderation/reports/{id}` | yes | One report with its history |
| PATCH | `/moderation/reports/{id}/status` | yes | Change the status (optional message) |
| POST | `/moderation/reports/{id}/updates` | yes | Add a message without changing the status |

Categories: `SECURITY`, `HARASSMENT`, `CORRUPTION`, `TECHNICAL`, `OTHER`

Status flow:
```
SUBMITTED -> UNDER_REVIEW -> RESOLVED
                          -> DISMISSED
```
`RESOLVED` and `DISMISSED` are final, a closed case can't be opened again.

Status codes: 200, 201, 400 (not allowed status change), 401 (no/bad token or wrong login),
403 (wrong invite code), 404 (not found), 409 (duplicate user or closed case),
422 (invalid input), 500 (server error, generic message only).

## Examples

Submit a report: `POST /reports`
```json
{
  "category": "CORRUPTION",
  "description": "Bribes are taken in the procurement office.",
  "evidence_url": "https://example.com/proof"
}
```
Response (201):
```json
{
  "case_code": "WD-1C9FD30A8917E65F",
  "status": "SUBMITTED",
  "message": "Report submitted. Save your case code, it cannot be recovered."
}
```

Track it: `POST /reports/track`
```json
{"case_code": "WD-1C9FD30A8917E65F"}
```
Response (200):
```json
{
  "category": "CORRUPTION",
  "status": "UNDER_REVIEW",
  "created_at": "2026-10-03T14:32:04.960471Z",
  "updated_at": "2026-10-03T14:32:05.622394Z",
  "updates": [
    {"status": "SUBMITTED", "message": "Report received", "created_at": "2026-10-03T14:32:04.960471Z"},
    {"status": "UNDER_REVIEW", "message": "Investigation started", "created_at": "2026-10-03T14:32:05.622394Z"}
  ]
}
```

Login: `POST /auth/login`
```json
{"username": "alice", "password": "password123"}
```
Response: `{"access_token": "<jwt>", "token_type": "bearer"}`

Change status: `PATCH /moderation/reports/1/status` with header `Authorization: Bearer <jwt>`
```json
{"status": "UNDER_REVIEW", "message": "Investigation started"}
```

Not allowed change (for example UNDER_REVIEW -> SUBMITTED) gives 400:
```json
{"detail": "Cannot change status from UNDER_REVIEW to SUBMITTED. Allowed: RESOLVED, DISMISSED"}
```

## Anonymity

- Reporters never log in. `POST /reports` is public.
- The `reports` table has no link to a user and no IP address column. Nobody (not even a moderator
  with database access) can find out who wrote a report from the data we store.
- Case codes are random (`secrets.token_hex(8)`, 64 bits), so they can't be guessed.
- Only a SHA-256 hash of the case code is saved. If the database leaks, the real codes are still unknown.
  The real code is shown once, when the report is submitted.
- The case code is sent in the request body (`POST /reports/track`) and not in the URL, because URLs end up in logs.
- Tracking returns only category, status and updates. It does not return the description or the evidence link.
- `run.py` turns off Uvicorn's access log, since that log prints the IP of every request.
- Wrong case codes always give the same 404 message.

Limits: this project does not control what happens outside the app. A reverse proxy, hosting
platform or the network can still log IP addresses.

## Assumptions and design decisions

- Only moderators have accounts. Registration needs an invite code from `.env`, otherwise anybody could
  become a moderator. A real system would let an admin create moderators.
- All moderators have the same permissions. There is no separate admin role.
- A lost case code can't be recovered, because we don't know who the reporter is and only store the hash.
- Messages added by moderators are visible to the reporter, so they shouldn't contain private notes.
- Tables are created with `create_all` at startup. There is no migration tool because the project is small.
- bcrypt only supports passwords up to 72 bytes, so longer passwords are rejected.
- Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (60 by default).
- Not done: rate limiting, file upload, deployment.

## Extra features

- Closed cases are permanent
- Case code stored as hash
- Search, filters and pagination for moderators
- Stats endpoint (small dashboard)
- Swagger docs at `/docs`
- pytest tests

## Screenshots

**Swagger overview**
![Swagger overview](screenshots/01-swagger-overview_(1).png)
                    (screenshots/01-swagger-overview_(2).png)
                    (screenshots/01-swagger-overview_(3).png)

**Submitting an anonymous report**
![Submit report](screenshots/02-submit-report.png)

**Tracking a report with the case code**
![Track report](screenshots/03-track-report.png)

**Moderator login**
![Moderator login](screenshots/04-moderator-login.png)

**Listing and filtering reports**
![List reports](screenshots/05-list-reports.png)

**Changing the status**
![Change status](screenshots/06-change-status.png)

**Reporter sees the moderator's update**
![Track after update](screenshots/07-track-after-update.png)

**Error handling**
![Error case](screenshots/08-error-case.png)

**Tests**
![pytest result](screenshots/09-pytest.png)
