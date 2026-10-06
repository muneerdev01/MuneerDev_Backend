"""
Resend Email Service
Path: app/core/email.py
"""
import os
from datetime import datetime
import resend

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "orders@yourdomain.com")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

async def send_download_link_email(
    to_email: str,
    product_title: str,
    download_url: str,
    expires_at: datetime
) -> dict:
    """Sends a responsive HTML transactional email with the 24-hr download link."""
    formatted_date = expires_at.strftime("%B %d, %Y at %H:%M UTC")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8" /></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, sans-serif; background-color: #0a0a0a; color: #f5f5f5; padding: 40px 20px;">
      <div style="max-width: 560px; margin: 0 auto; background: #171717; border: 1px solid #262626; border-radius: 12px; padding: 32px;">
        <h1 style="color: #10b981; font-size: 22px; margin-top: 0;">Thank you for your purchase!</h1>
        <p style="color: #d4d4d4; font-size: 14px; line-height: 1.6;">
          Your digital pattern <strong>{product_title}</strong> is ready for download.
        </p>
        <div style="text-align: center; margin: 32px 0;">
          <a href="{download_url}" style="background-color: #10b981; color: #0a0a0a; font-weight: 600; text-decoration: none; padding: 14px 28px; border-radius: 8px; font-size: 14px; display: inline-block;">
            Download Pattern (PDF/ZIP)
          </a>
        </div>
        <p style="color: #a3a3a3; font-size: 12px; line-height: 1.5; border-top: 1px solid #262626; padding-top: 16px;">
          ⏱ <strong>Notice:</strong> This secure download link is valid for <strong>24 hours</strong> (expires {formatted_date}).
        </p>
      </div>
    </body>
    </html>
    """

    params: resend.Emails.SendParams = {
        "from": RESEND_FROM_EMAIL,
        "to": [to_email],
        "subject": f"Your digital download: {product_title}",
        "html": html_content,
    }

    return resend.Emails.send(params)
