# HifzAI backend (Phases 10–28)

FastAPI + PostgreSQL, replacing the frontend's mock data and per-browser
`localStorage` with real accounts and a shared database. See the root
`README.md`'s Phase 10 section for how this maps onto each earlier phase's
"mock now, swap later" notes.

## Stack

- **FastAPI** for the HTTP API
- **SQLAlchemy 2.0** for models/queries
- **PostgreSQL** in any real deployment (SQLite is also supported, purely
  so this can be run with zero external services for a quick local check —
  see `DATABASE_URL` below)
- **JWT** bearer tokens for auth (`python-jose` + `bcrypt` for hashing)
- Practice-attempt audio saved to local disk under `MEDIA_ROOT`, served
  back via a static file mount

## Running it

### Option A — Docker Compose (Postgres included)

```bash
cd backend
docker compose up --build
```

Migrations run automatically as part of the container's start command
(see `Dockerfile`) before Postgres and the API together. The API is then
at `http://localhost:8000`. To seed demo data into the running container:

```bash
docker compose exec api python -m app.seed
```

### Option B — local Python, SQLite (zero setup)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt      # add requirements-dev.txt too if running tests
cp .env.example .env
# edit .env: DATABASE_URL=sqlite:///./hifzai.db
alembic upgrade head         # Phase 17: schema now comes from migrations, not create_all
python -m app.seed           # demo accounts
uvicorn app.main:app --reload
```

### Option C — local Python, real Postgres

Same as B, but point `DATABASE_URL` in `.env` at a Postgres instance you
already have running (e.g. `postgresql+psycopg2://user:pass@localhost:5432/hifzai`)
instead of editing it to SQLite.

### Running tests

```bash
pip install -r requirements-dev.txt   # pytest, on top of the normal requirements
pytest
```

Tests run against an isolated in-memory SQLite database (see
`tests/conftest.py`) — they never touch whatever `DATABASE_URL` points at,
so it's safe to run against a dev database with real seeded data.

## Demo accounts

`app/seed.py` creates a demo organization (`HifzAI Demo Academy`, slug
`hifzai-demo`) and the same people the frontend used to mock
(`mockDashboard.ts`, `mockStudents.ts`, `mockTeachers.ts`) as real rows
inside it, all sharing one password:

| Role    | Email                          | Notes                          |
|---------|---------------------------------|---------------------------------|
| Student | yusuf.student@hifzai.demo        | 12-day streak, mid Al-Baqarah   |
| Student | amina.student@hifzai.demo        | 21-day streak                   |
| Student | omar.student@hifzai.demo         | broken streak (shows up in Admin's "needs attention") |
| Teacher | bilal.teacher@hifzai.demo        | teaches Halaqah 1 (Yusuf, Amina)|
| Teacher | maryam.teacher@hifzai.demo       | teaches Halaqah 2 (Omar)        |
| Parent  | parent@hifzai.demo               | linked to Yusuf Ahmed           |
| Admin   | admin@hifzai.demo                 | sees all teachers/classes/students |

Password for all of them: `hifzai-demo-2026`

To register a *new* account into this same demo organization (rather than
creating a new one), use organization code `hifzai-demo` at registration.

## API shape

Everything is under camelCase JSON (a `CamelModel` base class aliases
every field) so the existing frontend TypeScript types didn't need
renaming to match.

- `POST /auth/register` (requires `organizationSlug` to join an existing
  org, or `organizationName` to create a new one as an admin — see
  Phase 18 below), `POST /auth/login` → access + refresh token pair
- `POST /auth/refresh` — rotates the refresh token, issues a new access
  token (Phase 17; access tokens are now short-lived, 15 min by default)
- `POST /auth/logout` — revokes a refresh token
- `POST /auth/request-password-reset`, `POST /auth/reset-password` —
  Phase 17; emails a reset link via the same SMTP integration Phase 16 built
- `GET /me/dashboard`, `GET /me/progress`
- `GET/POST /me/practice-attempts` (multipart, optional audio file)
- `GET/POST /me/test-sessions`
- `GET /me/reviews/due` — SM-2-scheduled spaced-repetition reviews (Phase 13)
- `POST /me/practice-attempts/{id}/analyze` — recitation analysis (Phase
  14; requires `OPENAI_API_KEY`, returns a failed-status result if unset)
- `GET /me/gamification` — XP, level, achievements (Phase 15)
- `GET /me/leaderboard?scope=class|all` — ranked by XP (Phase 15)
- `GET /notifications`, `POST /notifications/{id}/read`,
  `POST /notifications/read-all` — any role, not student-only (Phase 16)
- `GET /notifications/vapid-public-key`,
  `POST`/`DELETE /notifications/push-subscription` — Web Push opt-in
  (Phase 16; requires `VAPID_PUBLIC_KEY`/`VAPID_PRIVATE_KEY`)
- `GET /teacher/roster`, `GET /teacher/students/{id}`,
  `POST /teacher/students/{id}/sabaq`, `POST /teacher/students/{id}/feedback`
- `GET /parent/children`, `GET /parent/children/{id}/overview`
- `GET /admin/teachers`, `GET /admin/classes`, `GET /admin/students`,
  `GET /admin/analytics`, `POST /admin/classes`,
  `POST /admin/students/{id}/class` — all organization-scoped (Phase 18)
- `GET /admin/audit-log` — the real security audit trail (Phase 17),
  also organization-scoped
- `GET /admin/organization`, `PATCH /admin/organization` — the admin's
  own org: plan, seat usage vs. limits, name/branding (Phase 18)
- `GET /organizations/{slug}/public` — unauthenticated; name + branding
  only, for the login page (Phase 18)
- `GET /me/analytics/advanced` — weakest juz/surah/pages, most-forgotten
  ayah, retention rate, confidence score (Phase 21)
- `POST /me/tests/generate` — generates a question for any of 12 test
  modes from real completed Sabaqs (Phase 22)
- `GET /me/assistant/messages`, `POST /me/assistant/messages` — the AI
  tutor (Phase 24; requires `OPENAI_API_KEY`, same key as Whisper)
- `GET /me/notes`, `POST /me/notes`, `DELETE /me/notes/{id}` — Phase 26,
  offline-queue-aware via `clientMutationId`
- `GET /me/live-sessions/active` — is there a live class for my class
  right now (Phase 25)
- `POST /teacher/live-sessions`, `GET /teacher/live-sessions/active`,
  `POST /teacher/live-sessions/{id}/end`,
  `GET /teacher/live-sessions/{id}/report`, `GET /teacher/classes`
  (Phase 25)
- `WS /ws/live-sessions/{id}?token=...` — WebRTC signaling (Phase 25;
  not a REST endpoint, see below)
- `GET /me/certificates`, `GET /me/certificates/{id}/pdf` — real PDF
  certificates, lazily auto-detected for surah/juz completion (Phase 27)
- `POST /teacher/students/{id}/certificates` — issues an attendance or
  competition certificate (a human judgment call, unlike auto-detected
  completion certificates)
- `GET /me/conversations`, `POST /me/conversations`,
  `GET`/`POST /me/conversations/{id}/messages` — direct messaging
  between a teacher and a student/parent with a real relationship to
  their class (Phase 28)
- `GET /me/announcements`, `GET /me/homework`,
  `POST /teacher/announcements`, `POST /teacher/homework`,
  `POST /admin/announcements` (institution-wide only)

Interactive docs are at `http://localhost:8000/docs` once it's running.

## What's real now vs. still simplified

Real, as of this phase:
- Accounts, passwords, and JWT auth — no more mock roster or hardcoded
  parent-child link
- Streak, practice/test history, and progress analytics — computed
  server-side from actual recorded rows, shared across every portal
  instead of living in one browser's `localStorage`
- Teacher → student scoping by real class enrollment, not a flat mock list
- Practice-attempt audio upload and playback (Phase 7 flagged this as
  missing; it's now saved to disk and served back)
- **Sabqi/Manzil review scheduling** (Phase 13) — real SM-2 spaced
  repetition (`services/spaced_repetition.py`), graded from actual Test
  Mode scores, not the earlier heuristic. SM-2 over FSRS deliberately:
  FSRS needs a real corpus of review-outcome data to fit its parameters,
  which doesn't exist yet; SM-2 is a fixed, published algorithm that's
  correct without training data.
- **Recitation analysis** (Phase 14) — an explicit, on-demand action that
  transcribes a practice recording via OpenAI's Whisper API and word-diffs
  it against the real ayah text (fetched live, same principle as the
  frontend's `quranTextService.ts` — see `services/quran_text.py`).
  Detects missing/extra/substituted *words*; genuinely useful, genuinely
  real, and clearly scoped — see the limits below.
- **XP, levels, and achievements** (Phase 15) — computed from real
  recorded activity (practice attempts, test sessions, completed Sabaqs,
  streak), not a separate mutable balance that could drift. See
  `services/gamification.py`'s module docstring for the exact XP weights.
- **Notifications** (Phase 16) — real, event-driven in-app notifications
  (a teacher's feedback or new Sabaq assignment notifies the student
  immediately) plus two scheduled jobs (`app/scheduler.py`): a daily
  check for overdue reviews / at-risk streaks, and a weekly parent digest
  composed from the same real data the Parent Portal shows. Web Push
  (VAPID) and SMTP email are both real integrations, both optional and
  gracefully absent (not a crash) when their env vars are unset.
- **Production hardening** (Phase 17):
  - **Alembic migrations** replace `create_all` — see `alembic/versions/0001_initial_schema.py`
  - **Refresh tokens with rotation**: access tokens now expire in 15
    minutes; a refresh token (hashed before storage, same principle as
    passwords) issues a new pair and revokes itself, so a stolen refresh
    token is only replayable once before it's caught
  - **Real account lockout**: 5 failed logins locks the account for 15
    minutes, independent of and with a higher threshold than the login
    rate limit, so the two defenses don't collide
  - **Rate limiting** (`slowapi`, in-memory) on login/register/password-reset
  - **Password reset**, actually wired to the real SMTP integration from
    Phase 16 — never reveals whether an email is registered, and a
    successful reset revokes every existing refresh token for that user
  - **A real audit log** (`audit_log_entries`) recording login attempts,
    lockouts, registrations, refreshes, logouts, and password resets —
    visible read-only in the Admin Portal, not just sitting unused in a table
  - **A real automated test suite** (`tests/`, run with `pytest`) covering
    the auth flow end-to-end plus the SM-2, Arabic-diff, streak, and
    gamification logic — see "Running tests" above
- **Multi-tenancy** (Phase 18): every user belongs to exactly one
  `Organization` — the tenant boundary every multi-user query (admin
  lists/analytics/audit-log, the "all" leaderboard scope) is now scoped
  to. An admin registering with `organizationName` creates a new
  organization; anyone else registers by joining an existing one via
  `organizationSlug`, subject to real plan-limit enforcement
  (`max_students`/`max_teachers`, checked at registration, not just
  displayed). Cross-tenant isolation is covered by real tests
  (`tests/test_tenancy.py`) — an admin from one organization genuinely
  cannot see another organization's students, teachers, classes, or audit
  log, and can't assign a class to a teacher from a different org.
- **Advanced analytics** (Phase 21) — weakest juz/surah/pages, most-
  forgotten ayah, retention rate, and a documented confidence-score
  formula, all computed from real `TestResult`/`ReviewSchedule` rows.
  Weakest-juz/page bucketing needed to know which juz/page each tested
  ayah falls on — extended `quran_text.py`'s live-fetch-and-cache
  pattern (same "never hand-type positional data" principle as Phase 12)
  rather than adding a static table.
- **Advanced test modes** (Phase 22) — 12 real test modes generated from
  the student's own completed Sabaqs, not scripted content. They reduce
  to two interaction types reused across all of them: "recite" (the
  existing hide/listen/record/self-mark flow, just over a different ayah
  range) and "multiple_choice" (a prompt + 4 real choices, answer
  revealed immediately — self-study, not a proctored exam, same trust
  model as the rest of Test Mode). See `services/test_modes.py`'s module
  docstring.
- **AI assistant** (Phase 24) — a real chat-completions integration with
  function-calling (`services/llm_service.py`, `services/assistant_service.py`).
  The model can call tools that run real backend logic (`get_weak_spots`,
  `get_due_reviews`, `get_progress_summary`) and is instructed, via a
  system prompt, to ground any answer about the student's own progress in
  what those tools actually return — never inventing a missed-page count
  or a "generated" revision schedule that isn't the real SM-2 due list.
  General Quran/tajweed questions are answered from the model's own
  knowledge with an explicit caveat that it isn't a substitute for a
  qualified teacher's in-person correction. One ongoing conversation per
  student, persisted (`chat_conversations`/`chat_messages`), not a
  stateless one-off request.
- **Live classes** (Phase 25) — real, audio-only, peer-to-peer WebRTC
  between a teacher's browser and however many students join, signaled
  through a real WebSocket endpoint (`/ws/live-sessions/{id}`) this
  backend hosts itself — no third-party video/calling service. Mesh
  ("hub") topology: every student connects directly to the teacher, which
  is realistic for a halaqah-sized class but won't scale to a large
  lecture without a real SFU media server, a materially bigger separate
  project. STUN only (Google's public server) — no TURN relay is run, so
  a student behind a very restrictive/symmetric NAT may simply fail to
  connect; running TURN is real deployed infrastructure with bandwidth
  costs, not something buildable as application code. Attendance is
  genuinely automatic (`live_session_participants.joined_at`/`left_at`
  set by the actual WebSocket connection lifecycle, not a manual
  checkbox), and mistake marks the teacher makes live are persisted and
  summarized in a real end-of-session report.
- **Offline-first** (Phase 26) — a real IndexedDB-backed mutation queue
  (`offlineQueueDb.ts`/`offlineSyncService.ts` on the frontend): practice
  attempts, test sessions, and notes saved while offline are queued
  locally and synced automatically once connectivity returns, using a
  client-generated `client_mutation_id` so a retried sync can never
  create a duplicate row (checked server-side on `practice_attempts`,
  `test_sessions`, and `notes`). Quran text/pages and the last-synced
  Dashboard/Progress views are cached to IndexedDB too, so they're
  viewable offline after a first online visit. The service worker
  (`public/sw.js`) now does real app-shell caching (cache-as-you-go, not
  a build-time precache manifest — see the file's own comment for why),
  extending what Phase 16 explicitly scoped out.
- **Certificates** (Phase 27) — real PDF generation (`reportlab`) for
  four types. `surah_completion`/`juz_completion` are auto-detected,
  lazily, on every `GET /me/certificates` (same self-healing pattern
  Phase 15's achievements established) — computed from real completed-
  Sabaq ayah coverage checked against the real surah ayah count / real
  juz composition (both fetched live via `quran_text.py`, extended in
  this phase with a `get_juz_ayahs()` lookup rather than a hand-typed
  table). `attendance`/`competition` require a teacher's explicit
  judgment call — issued, not auto-detected. Each certificate's PDF is
  rendered on demand from the organization's real branding (Phase 18's
  `primary_color`/`logo_url`), never stored. "Teacher signed" means the
  teacher's real name printed on a signature line in a signature-styled
  font — no uploaded/scanned signature image or e-signature flow was
  built, stated plainly rather than implied.
- **Communication** (Phase 28) — real direct messaging, restricted to
  teacher-student and teacher-parent pairs with an actual relationship to
  the teacher's class (`services/messaging_service.py`'s `can_message()`
  — two students, or a teacher and someone outside their classes, cannot
  message each other). Announcements (class-scoped by a teacher,
  institution-wide by an admin) and homework (class-scoped, due-dated)
  are both real, persisted, and role-aware on read. Voice notes and file
  attachments reuse Phase 10's local-disk media storage, extended to a
  generic message-attachment path — voice notes are audio *file
  uploads*, not a dedicated in-message recorder (Practice Mode's live
  `useRecorder` wasn't duplicated here, a deliberate scope choice).

Still simplified, on purpose, and worth knowing before treating this as
production-ready:
- Media storage is local disk, not S3/CDN — fine for one server, not for
  horizontal scaling or durability.
- **Spaced repetition operates at Sabaq granularity**, not per-ayah —
  coarser than some systems, but consistent with how the rest of the app
  already organizes memorization units.
- **Recitation analysis is word-diffing, not Tajweed analysis.** It
  cannot verify vowelization/tashkeel correctness (diacritics are
  stripped before comparison), can't assess elongation/ghunnah/qalqalah/
  articulation, and depends on Whisper — a general-purpose STT model, not
  one tuned for Quranic recitation — accurately transcribing the audio in
  the first place. It costs money per call (why it's on-demand, not
  automatic). See `services/arabic_text.py`'s module docstring for the
  full, specific list of what this can and can't tell you.
- **XP weights are round, undocumented-elsewhere numbers**, not tuned
  against any real engagement data (there isn't any yet). They're
  transparent and easy to change (`services/gamification.py`), just not
  the product of A/B testing or analytics.
- **The "all" leaderboard scope is organization-wide** (Phase 18 added
  real multi-tenancy after this was originally written as "there's no
  multi-tenancy yet" — it now correctly scopes to the student's own
  organization, not the whole database).
- **The scheduler is in-process** (`APScheduler`'s `BackgroundScheduler`,
  started on app startup) — fine for one server, but running more than
  one instance of this app would run the daily/weekly jobs once per
  instance rather than once overall. A real horizontally-scaled
  deployment needs a proper job queue (Celery/RQ + a broker) instead.
- **Notification dedup is "once per day per type," not smarter than
  that** — `already_notified_today` prevents spam within a single day but
  doesn't do anything more nuanced (e.g. escalating urgency, snoozing).
- **No email verification** — registering with any email address works
  immediately; nothing confirms you actually control that inbox. Password
  reset links are the only thing gated on real email access.
- **Rate limiting is in-memory, per-instance** (`slowapi`'s default
  storage) — same caveat as the scheduler: correct for one server, not
  enforced globally across multiple instances without pointing it at a
  shared Redis backend instead.
- **The test suite is real but not exhaustive** — it covers the auth
  flow and the pure-logic modules (SM-2, Arabic diffing, streak,
  gamification) with real assertions, not a smoke test. It does not cover
  every endpoint (teacher/parent/admin routers beyond the tenancy tests,
  notifications, the scheduler's job bodies) — a reasonable next
  increment, not something to assume is covered because "there are tests now."
- **No billing/payment collection** (Phase 18). Plan limits
  (`max_students`/`max_teachers`) are real and enforced at registration,
  but upgrading an organization's `plan` today is a manual database
  update — there's no Stripe/Paddle integration, no checkout flow, no
  self-serve upgrade button. Building real payment collection is a
  substantially different, larger piece of work than the tenancy model
  itself, and wasn't attempted.
- **No self-serve "create my organization" page.** The polished
  `LoginPage` registration form only supports *joining* an existing
  organization (an organization code, i.e. slug, is required) —
  consistent with admin accounts never being self-serve in earlier
  phases either. Creating a new organization (`role: admin` +
  `organizationName`) works via the API today but has no dedicated
  frontend page.
- **Organization branding (`primaryColor`/`logoUrl`) has a real data
  model and a public read endpoint, but no theming engine consumes it.**
  The login page doesn't yet fetch and apply an organization's branding
  before authentication — the field exists and is settable via
  `PATCH /admin/organization`, but nothing renders it yet.
- **Tenant scoping covers the queries that actually list across
  multiple users** (admin lists/analytics/audit-log, the "all"
  leaderboard) — it does not add an `organization_id` column to every
  single table. Sabaqs/practice attempts/test sessions/etc. stay scoped
  through the student they belong to, which is sufficient because every
  query against them is already scoped to one specific student (via
  `get_current_student_profile`, a teacher's class roster, or a parent's
  linked child) — not because tenancy was left half-applied.
- **`confidence_score` is a formula, not a model.** Stated plainly, not
  buried: `0.6 * retention_rate + 0.4 * overall_accuracy`, with weights
  chosen for being a reasonable, explainable blend, not fit against any
  labeled ground truth (none exists for "how confident should this
  student feel"). Same honesty standard as the gamification XP weights.
- **Weakest-juz/page/most-forgotten-ayah rankings require a minimum of 2
  recorded attempts** (`MIN_ATTEMPTS_FOR_RANKING`) before an item is
  eligible — otherwise a single unlucky miss on something tested once
  would dominate the ranking. A new student with little Test Mode history
  will see mostly empty analytics, honestly, rather than a ranking built
  on a sample size of one.
- **The new test modes' live juz/page/surah-list lookups aren't covered
  by automated tests** — same network-dependent-code limitation Phase 14
  already had for recitation analysis; only the DB-only logic (which
  Sabaq gets picked, empty-state handling) is tested.
- **Multiple-choice test questions are not proctored.** The correct
  answer is sent to the client immediately on generation — deliberately,
  to match the trust model Test Mode's self-marked recitation has used
  since Phase 5, not an oversight. This app has never tried to prevent
  self-study "cheating"; building server-side answer-hiding/grading would
  be inconsistent with that, not a missing feature.
- **Visual memorization's "line" hiding (Phase 23) is a browser-reflow
  line, not a fixed printed page's line** — it's computed client-side
  from wherever the text currently wraps, and will regroup differently
  on a different screen width. A real hafiz's "hide line 3" technique
  depends on a fixed, memorized page image, which this app still doesn't
  render (same limitation Phase 12 already had for page-based Mushaf
  viewing). This is a genuinely useful digital variant of the technique,
  not the identical thing.
- **The assistant's tool-calling loop caps at 4 rounds**
  (`MAX_TOOL_ROUNDS`) and isn't covered by automated tests, since testing
  it end-to-end means testing a live LLM API — same network-dependent-code
  limitation Phase 14's recitation analysis and Phase 21/22's live
  juz/page lookups already have. Only the DB-only conversation-persistence
  logic (`tests/test_assistant.py`) is tested.
- **The assistant has exactly 3 tools** (weak spots, due reviews,
  progress summary) — it cannot yet take actions on the student's behalf
  (e.g. actually assigning a Sabaq, marking something complete), only
  read and discuss real data. Read-only by design for this phase, not a
  missing "write" capability that got forgotten.
- **Live sessions have no TURN server.** STUN-only WebRTC (see Phase 25's
  note above) means some students, depending on their network, may fail
  to connect — a real, known category of failure this app cannot fully
  solve without deployed relay infrastructure.
- **Live-session signaling is in-process**, same caveat as the scheduler
  and rate limiter: the WebSocket connection registry
  (`services/live_session_connections.py`) lives in one server's memory.
  Running more than one backend instance without a shared pub/sub would
  split a class's teacher and students across processes that can't relay
  signaling to each other.
- **Live sessions are audio-only, mesh topology, small-class-sized.**
  No video, no recording. Every student connects directly to the
  teacher's browser rather than through a media server, which is
  realistic for a halaqah but won't hold up for a large lecture — that
  would need a real SFU (e.g. mediasoup, LiveKit), a substantially
  bigger separate project, not an incremental extension of this one.
- **The offline queue handles practice attempts, test sessions, and
  notes — not every mutation in the app.** Feedback, Sabaq assignment,
  gamification, and most teacher/admin/parent actions still require a
  live connection; those weren't in the original "Progress ✓ Tests ✓
  Notes" list and extending offline support to all of them would be a
  much larger undertaking.
- **App-shell offline caching is cache-as-you-go, not a precache.** The
  app becomes available offline only after a page/asset has been
  fetched online at least once — there's no build-time precache manifest
  (would need a tool like `vite-plugin-pwa`), a deliberate, documented
  trade-off, not an oversight.
- **None of Phase 25's WebSocket/WebRTC signaling code, and none of
  Phase 26's IndexedDB-based caching/queueing, is covered by automated
  tests** — both require a real browser runtime (WebRTC, IndexedDB) that
  this backend's pytest suite doesn't have access to. Phase 25's REST
  lifecycle (start/end/report, access control) is tested
  (`tests/test_live_sessions.py`); the actual signaling exchange is not,
  the same honest limitation every other live-network-dependent piece of
  this app already carries.
- **Certificate PDFs have no e-signature or uploaded signature image** —
  "teacher signed" is a printed name in a signature-styled font. A real
  digital-signature flow (or letting a teacher upload a scanned
  signature) would be a genuinely separate, larger feature.
- **Only surah and juz completion are auto-detected**; attendance and
  competition certificates require a teacher to issue them explicitly —
  there's no automated "5 live sessions attended" or "top of the
  leaderboard this month" trigger. Building that would mean defining and
  storing real milestone thresholds and competition date ranges, which
  wasn't attempted this phase.
- **Messaging is teacher-initiated only from the current UI.** The
  access-control rule (`can_message()`) allows either side to reply once
  a conversation exists, but the only UI for *starting* a new one is on
  the teacher's student-detail page — a student or parent can't yet
  browse and message their teacher first. A real, if narrower, next
  increment rather than a limitation of the access-control model itself
  (which supports either direction).
- **Voice notes in messages are file uploads, not a live recorder.**
  Practice Mode already has a real in-browser recorder (`useRecorder`);
  it wasn't reused for messaging to keep this phase's scope to the
  messaging/attachment plumbing itself, not a second recording UI.
- **Homework is a separate, simpler concept from Sabaqs** — a title,
  description, and due date, with no submission/grading flow. It's an
  assignment a teacher can post, not a graded piece of work a student
  turns back in through the app.
- **None of Phase 27/28's live-network-dependent pieces
  (juz-composition lookups, PDF logo fetching) are covered by automated
  tests**, the same limitation every other live-API-dependent phase
  already carries. The DB-only logic (ayah-coverage math, messaging
  access control — the highest-risk part, since a wrong check would let
  arbitrary users message each other) is tested
  (`tests/test_certificates.py`, `tests/test_messaging.py`).
