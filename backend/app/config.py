from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central config, read from environment variables / a .env file. Nothing
    here is hardcoded for a specific deploy — `DATABASE_URL` in particular
    is expected to point at Postgres in any real environment; SQLite is
    supported too (just point DATABASE_URL at a sqlite:/// file) purely so
    this can be run with zero external services for a quick local check.
    """

    database_url: str = "sqlite:///./hifzai.db"
    jwt_secret: str = "change-this-to-a-random-secret-in-production"
    jwt_algorithm: str = "HS256"
    # Phase 17: shortened from 24h now that refresh tokens exist — a
    # leaked access token is only useful for this long, not a full day.
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    # Phase 30: used instead of refresh_token_expire_days when the user
    # leaves "Stay signed in" unchecked at login — see routers/auth.py.
    # This is a backend-side ceiling; the frontend also stops the session
    # earlier than this by keeping the token in sessionStorage, which is
    # cleared as soon as the tab/browser closes.
    short_refresh_token_expire_days: int = 1
    cors_origins: str = "http://localhost:5173"
    media_root: str = "./media"

    # Phase 17: account lockout after repeated failed logins.
    max_failed_login_attempts: int = 5
    account_lockout_minutes: int = 15

    # Phase 17: password reset links point back at the frontend, e.g.
    # `{frontend_url}/reset-password?token=...`.
    frontend_url: str = "http://localhost:5173"
    password_reset_token_expire_minutes: int = 30

    # Phase 14: recitation analysis (Whisper transcription + word-diff
    # against the reference ayah text). None by default — the feature is
    # cleanly disabled (a clear error, not fabricated results) when unset,
    # rather than requiring it to run this app at all.
    openai_api_key: str | None = None
    # Phase 24: the AI assistant reuses the same key — a chat-completions
    # model, not Whisper. gpt-4o-mini is a reasonable default (capable
    # enough for tool-calling, inexpensive for a study-assistant use case).
    assistant_chat_model: str = "gpt-4o-mini"

    # Phase 16: Web Push (VAPID keypair) — generate with
    #   python -c "from py_vapid import Vapid; v=Vapid(); v.generate_keys(); print(v.private_key, v.public_key)"
    # or the `pywebpush`-recommended tooling. None by default: push sends
    # are silently skipped (in-app notifications still work) rather than
    # erroring, since not every deployment needs push.
    vapid_public_key: str | None = None
    vapid_private_key: str | None = None
    vapid_admin_email: str = "admin@example.com"

    # Phase 16: SMTP for the weekly parent email digest. Optional — if
    # `smtp_host` is unset, email sends are skipped (logged, not raised);
    # the in-app notification is still created either way.
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_address: str = "hifzai@example.com"

    # Phase 32: billing. None by default — same "cleanly disabled, not
    # fabricated" pattern as openai_api_key above. Without a secret key,
    # /admin/billing/checkout-session returns a clear 503 rather than
    # pretending to create a real Stripe session.
    stripe_secret_key: str | None = None
    # Verifies that incoming /webhooks/stripe requests genuinely came from
    # Stripe (not spoofed) — see services/billing.py's verify_webhook_signature.
    stripe_webhook_secret: str | None = None
    # The Stripe Price ID for the "pro" plan's monthly subscription,
    # created once in the Stripe Dashboard (Products -> Pricing) — this
    # app doesn't create Prices itself, it only references one that
    # already exists there.
    stripe_pro_price_id: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
