import logging
import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv


class EmailNotifier:
    def __init__(self, env_file=None):
        load_dotenv(env_file)

        self.enabled = os.getenv(
            "EMAIL_ENABLED", "yes"
        ).strip().lower() in {"yes", "true", "1", "on"}

        self.smtp_server = os.getenv("EMAIL_SMTP_SERVER")
        self.smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self.username = os.getenv("EMAIL_USERNAME")
        self.password = os.getenv("EMAIL_PASSWORD")
        self.recipient = os.getenv("EMAIL_RECIPIENT")

    def validate(self):
        if not self.enabled:
            logging.warning("Email notifications are disabled.")
            return False

        missing = []
        values = {
            "EMAIL_SMTP_SERVER": self.smtp_server,
            "EMAIL_USERNAME": self.username,
            "EMAIL_PASSWORD": self.password,
            "EMAIL_RECIPIENT": self.recipient,
        }

        for key, value in values.items():
            if not value:
                missing.append(key)

        if missing:
            raise RuntimeError(
                "Email configuration incomplete: " +
                ", ".join(missing)
            )

        return True

    def send_message(self, subject, body):
        if not self.enabled:
            return False

        self.validate()

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.username
        message["To"] = self.recipient
        message.set_content(body)

        try:
            with smtplib.SMTP(
                self.smtp_server,
                self.smtp_port,
                timeout=15
            ) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(
                    self.username,
                    self.password
                )
                server.send_message(message)

            logging.info(
                "Email sent successfully: %s",
                subject
            )
            return True

        except Exception:
            logging.exception("Email sending failed")
            return False
