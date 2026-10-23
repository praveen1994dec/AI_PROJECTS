"""SMTP delivery for budget threshold alerts."""
from __future__ import annotations

import asyncio
import os
import smtplib
from email.message import EmailMessage
from typing import Any, Dict


def smtp_configured() -> bool:
    return all(os.getenv(key) for key in ("SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM"))


def _send_sync(recipient: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = os.environ["SMTP_FROM"]
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"]), timeout=20) as server:
        if os.getenv("SMTP_TLS", "true").lower() == "true":
            server.starttls()
        server.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"])
        server.send_message(message)


async def send_budget_alert(recipient: str, region: str, status: str, summary: Dict[str, Any]) -> None:
    body = (
        f"Your {region} budget is {status}.\n\n"
        f"Budget: ${float(summary['monthly_budget']):.2f}\n"
        f"Spent: ${float(summary['mtd_spend']):.2f}\n"
        f"Usage: {float(summary['percent_used']):.1f}%\n"
        f"Forecast: ${float(summary['forecasted_month_end_spend']):.2f}\n"
    )
    await asyncio.to_thread(_send_sync, recipient, f"AWS budget {status}: {region}", body)