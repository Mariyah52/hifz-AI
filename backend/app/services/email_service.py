import logging
import smtplib
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(to_address: str, subject: str, body_text: str) -> bool:
    """
    Deliberately stdlib-only (`smtplib`) rather than a paid transactional-
    email API — this app has zero required external dependencies for
    email, only an SMTP relay you point it at (your own mail server, or
    any provider's SMTP endpoint). Returns False and logs, rather than
    raising, when unconfigured or on send failure — email delivery
    problems should never break the caller (see scheduler.py's weekly
    digest, the only real caller of this).
    """
    if not settings.smtp_host:
        logger.info("SMTP isn't configured — skipping email to %s: %s", to_address, subject)
        return False

    message = MIMEText(body_text)
    message["Subject"] = subject
    message["From"] = settings.smtp_from_address
    message["To"] = to_address

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.smtp_from_address, [to_address], message.as_string())
        return True
    except (smtplib.SMTPException, OSError) as exc:
        logger.warning("Failed to send email to %s: %s", to_address, exc)
        return False
