import os
import resend
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

router = APIRouter()

class ContactSchema(BaseModel):
    name: str
    email: str
    subject: str
    message: str

def send_resend_email(payload: ContactSchema):
    try:
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            print("ERROR: RESEND_API_KEY missing in environment variables")
            return

        resend.api_key = api_key
        response = resend.Emails.send({
            "from": "Portfolio Contact <onboarding@resend.dev>",
            "to": ["muneer.dev01@gmail.com"],  # Resend اکاؤنٹ والے ای میل پر بھیجیں
            "subject": f"Inquiry: {payload.subject}",
            "html": f"""
                <div style="font-family: Arial, sans-serif; padding: 20px; line-height: 1.6;">
                  <h2 style="color: #10b981;">New Contact Inquiry Received</h2>
                  <p><strong>Name:</strong> {payload.name}</p>
                  <p><strong>Email:</strong> {payload.email}</p>
                  <p><strong>Subject:</strong> {payload.subject}</p>
                  <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;" />
                  <p><strong>Message:</strong></p>
                  <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px;">
                    {payload.message}
                  </div>
                </div>
            """
        })
        print(f"Resend Transmission Success: {response}")
    except Exception as e:
        print(f"Resend Transmission Error: {e}")

@router.post("/contact")
async def send_contact_email(payload: ContactSchema, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_resend_email, payload)
    return {"status": "success", "message": "Inquiry recorded successfully"}