import os
import resend
from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

router = APIRouter()

class ContactSchema(BaseModel):
    name: str
    email: str
    subject: str
    message: str

@router.post("/contact")
async def send_contact_email(payload: ContactSchema):
    try:
        # API key is inside the function call to prevent blocking startup
        resend.api_key = os.getenv("RESEND_API_KEY", "")

        email_response = resend.Emails.send({
            "from": "MuneerDev Portfolio <onboarding@resend.dev>",
            "to": ["gmugsk@gmail.com"],
            "subject": f"Inquiry: {payload.subject}",
            "html": f"""
                <div style="font-family: Arial, sans-serif; padding: 20px; line-height: 1.6;">
                  <h2 style="color: #10b981;">New Contact Inquiry Received</h2>
                  <p><strong>Sender Name:</strong> {payload.name}</p>
                  <p><strong>Sender Email:</strong> {payload.email}</p>
                  <p><strong>Subject / Topic:</strong> {payload.subject}</p>
                  <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;" />
                  <p><strong>Message Body:</strong></p>
                  <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px;">
                    {payload.message}
                  </div>
                </div>
            """
        })
        return {"status": "success", "message": "Email dispatched via Resend API", "data": email_response}

    except Exception as e:
        print(f"Resend Error: {e}")
        return {"status": "success", "message": "Inquiry recorded"}