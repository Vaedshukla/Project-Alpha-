import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Iterable, Optional

from app.core.config import settings


_last_sent: dict[tuple[str, str], float] = {}


def _should_rate_limit(recipient: str, key: str) -> bool:
    window = max(1, settings.email_rate_limit_minutes) * 60
    k = (recipient, key)
    now = time.time()
    last = _last_sent.get(k)
    if last and now - last < window:
        return True
    _last_sent[k] = now
    return False


def send_email(subject: str, recipients: Iterable[str], body: str, html: Optional[str] = None, rate_key: Optional[str] = None) -> bool:
    recipients = list(recipients)
    if not recipients:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = ", ".join(recipients)

    msg.attach(MIMEText(body, "plain"))
    if html:
        msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.email_host, settings.email_port) as server:
            server.starttls()
            if settings.email_user and settings.email_pass:
                server.login(settings.email_user, settings.email_pass)
            # simple rate limiting per recipient and key
            for r in recipients:
                if rate_key and _should_rate_limit(r, rate_key):
                    continue
                server.sendmail(settings.email_from, r, msg.as_string())
        return True
    except Exception:
        return False

