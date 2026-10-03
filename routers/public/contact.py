"""
Contact form endpoint  ->  POST /api/v1/contact

Sends the inquiry through Resend's HTTPS API (port 443).
Do NOT use SMTP here: Render blocks outbound SMTP ports 25/465/587 on free services.
"""
import html
import logging
import os
from typing import Optional

import resend
from fastapi import APIRouter, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger("contact")

router = APIRouter(prefix="/contact", tags=["contact"])


class ContactRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    subject: Optional[str] = Field(default=None, max_length=200)
    message: Optional[str] = Field(default=None, max_length=5000)
    # Alternate field names, kept so older frontends keep working
    areaOfInquiry: Optional[str] = Field(default=None, max_length=200)
    projectScope: Optional[str] = Field(default=None, max_length=5000)


def _build_params(data: ContactRequest) -> dict:
    subject = data.subject or data.areaOfInquiry or "New Contact Inquiry"
    message = data.message or data.projectScope or "No details provided."

    # Escape everything user-supplied so nobody can inject HTML into your inbox
    e = html.escape
    body = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; line-height: 1.6;">
      <h2 style="color: #10b981;">New Contact Inquiry</h2>
      <p><strong>Name:</strong> {e(data.name)}</p>
      <p><strong>Email:</strong> {e(str(data.email))}</p>
      <p><strong>Subject:</strong> {e(subject)}</p>
      <hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0;" />
      <p><strong>Message:</strong></p>
      <div style="background:#f3f4f6;padding:15px;border-radius:8px;white-space:pre-wrap;">{e(message)}</div>
    </div>
    """

    return {
        # Until you verify your own domain in Resend, keep onboarding@resend.dev.
        # After verifying muneerdev.com, set RESEND_FROM="Portfolio <contact@muneerdev.com>"
        "from": os.getenv("RESEND_FROM", "Portfolio Contact <onboarding@resend.dev>"),
        # With onboarding@resend.dev, "to" MUST be the email you signed up to Resend with.
        "to": [os.getenv("CONTACT_TO_EMAIL", "muneer.dev01@gmail.com")],
        "reply_to": str(data.email),  # hitting Reply goes straight to the visitor
        "subject": f"[Portfolio] {subject}"[:250],
        "html": body,
    }


@router.post("", status_code=status.HTTP_200_OK)
async def send_contact_email(data: ContactRequest):
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.error("RESEND_API_KEY is not set on the server")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service is not configured. Please email me directly.",
        )

    resend.api_key = api_key
    params = _build_params(data)

    try:
        # resend SDK is synchronous -> run in a thread so the event loop is never blocked
        result = await run_in_threadpool(resend.Emails.send, params)
        logger.info("Contact email sent: %s", result)
    except Exception as exc:
        # Log the visitor's message too, so a lead is never lost if email fails
        logger.exception(
            "Resend failed: %s | lead: name=%r email=%r message=%r",
            exc, data.name, str(data.email), data.message or data.projectScope,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not send your message right now. Please try again shortly.",
        )

    return {"status": "success", "message": "Your message has been sent."}
