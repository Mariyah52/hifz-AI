from app.schemas.base import CamelModel


class DeleteAccountRequest(CamelModel):
    password: str
    confirm: bool  # frontend must force an explicit "yes, I understand this is permanent" checkbox


class DeleteAccountSummary(CamelModel):
    audio_files_deleted: int
    rows_hard_deleted: int
    messages_scrubbed: int


class RetentionPolicyOut(CamelModel):
    practice_test_audio: str
    messages: str
    audit_log: str
    deleted_accounts: str
