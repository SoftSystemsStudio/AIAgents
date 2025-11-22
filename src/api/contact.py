"""
Contact form API endpoints for lead generation.
"""
from datetime import datetime
from typing import Optional
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, validator
import logging
import resend

logger = logging.getLogger(__name__)

# Configure Resend
resend.api_key = os.getenv("RESEND_API_KEY", "")

router = APIRouter()


class ContactFormRequest(BaseModel):
    """Contact form submission data."""
    name: str
    email: EmailStr
    company: Optional[str] = None
    phone: Optional[str] = None
    service: str  # Which AI service they're interested in
    message: str
    budget: Optional[str] = None
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name is required')
        return v.strip()
    
    @validator('message')
    def message_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Message is required')
        return v.strip()
    
    @validator('service')
    def service_must_be_valid(cls, v):
        valid_services = [
            'customer-service-chatbot',
            'appointment-booking',
            'data-entry-processing',
            'email-social-automation',
            'custom-solution'
        ]
        if v not in valid_services:
            raise ValueError(f'Service must be one of: {", ".join(valid_services)}')
        return v


class ContactFormResponse(BaseModel):
    """Response after contact form submission."""
    success: bool
    message: str
    lead_id: str


# In-memory storage (will move to database later)
leads_db = {}
lead_counter = 1000


async def send_notification_emails(lead_data: dict, request: ContactFormRequest):
    """Send email notifications for new lead."""
    admin_email = os.getenv("ADMIN_EMAIL", "admin@softsystemsstudio.com")
    
    # Service name mapping
    service_names = {
        'customer-service-chatbot': 'Customer Service Chatbot',
        'appointment-booking': 'Appointment/Booking Automation',
        'data-entry-processing': 'Data Entry/Processing',
        'email-social-automation': 'Email/Social Media Automation',
        'custom-solution': 'Custom AI Solution'
    }
    service_name = service_names.get(request.service, request.service)
    
    try:
        # Email to admin/sales team
        admin_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #c0ff6b; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; color: #000;">🚀 New Lead!</h1>
            </div>
            <div style="background: #f5f5f5; padding: 30px; border-radius: 0 0 8px 8px;">
                <h2 style="color: #333;">Lead Details</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold;">Lead ID:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{lead_data['lead_id']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold;">Name:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{request.name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold;">Email:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><a href="mailto:{request.email}">{request.email}</a></td>
                    </tr>
                    {f'<tr><td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold;">Company:</td><td style="padding: 10px; border-bottom: 1px solid #ddd;">{request.company}</td></tr>' if request.company else ''}
                    {f'<tr><td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold;">Phone:</td><td style="padding: 10px; border-bottom: 1px solid #ddd;">{request.phone}</td></tr>' if request.phone else ''}
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold;">Service:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{service_name}</td>
                    </tr>
                    {f'<tr><td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold;">Budget:</td><td style="padding: 10px; border-bottom: 1px solid #ddd;">{request.budget}</td></tr>' if request.budget else ''}
                    <tr>
                        <td style="padding: 10px; font-weight: bold; vertical-align: top;">Message:</td>
                        <td style="padding: 10px;">{request.message}</td>
                    </tr>
                </table>
                <div style="margin-top: 20px; padding: 15px; background: #fff; border-left: 4px solid #c0ff6b;">
                    <strong>⏰ Action Required:</strong> Follow up within 24 hours for best conversion rates!
                </div>
            </div>
        </body>
        </html>
        """
        
        resend.Emails.send({
            "from": "Soft Systems Studio <noreply@softsystemsstudio.com>",
            "to": [admin_email],
            "subject": f"🎯 New Lead: {request.name} - {service_name}",
            "html": admin_html,
        })
        
        # Confirmation email to customer
        customer_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #000; padding: 30px; text-align: center;">
                <h1 style="margin: 0; color: #c0ff6b;">Soft Systems Studio</h1>
            </div>
            <div style="padding: 30px; background: #f5f5f5;">
                <h2 style="color: #333;">Thanks for reaching out, {request.name}! 👋</h2>
                <p style="font-size: 16px; line-height: 1.6; color: #555;">
                    We received your inquiry about <strong>{service_name}</strong> and we're excited to help automate your business!
                </p>
                <div style="background: #fff; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #c0ff6b;">
                    <h3 style="margin-top: 0; color: #333;">What happens next?</h3>
                    <ol style="color: #555; line-height: 1.8;">
                        <li>We'll review your requirements (typically within 2-4 hours)</li>
                        <li>Our team will reach out via email or phone</li>
                        <li>We'll schedule a free 30-minute consultation</li>
                        <li>You'll receive a custom proposal within 48 hours</li>
                    </ol>
                </div>
                <p style="font-size: 14px; color: #777;">
                    <strong>Your Reference ID:</strong> {lead_data['lead_id']}<br>
                    <strong>Service Requested:</strong> {service_name}
                </p>
                <div style="margin-top: 30px; padding: 20px; background: #c0ff6b; border-radius: 8px; text-align: center;">
                    <p style="margin: 0; color: #000; font-size: 14px;">
                        <strong>Questions in the meantime?</strong><br>
                        Reply to this email or call us at <strong>(555) 123-4567</strong>
                    </p>
                </div>
            </div>
            <div style="padding: 20px; text-align: center; color: #999; font-size: 12px;">
                <p>© 2025 Soft Systems Studio. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        resend.Emails.send({
            "from": "Soft Systems Studio <hello@softsystemsstudio.com>",
            "to": [request.email],
            "subject": "We received your inquiry - Soft Systems Studio",
            "html": customer_html,
        })
        
        logger.info(f"Emails sent successfully for lead {lead_data['lead_id']}")
        
    except Exception as e:
        logger.error(f"Failed to send emails for lead {lead_data['lead_id']}: {str(e)}")
        # Don't fail the request if email fails


@router.post("/contact", response_model=ContactFormResponse)
async def submit_contact_form(request: ContactFormRequest):
    """
    Handle contact form submission.
    
    This endpoint:
    1. Validates the submission
    2. Stores the lead in database
    3. Sends notification email to sales team
    4. Sends confirmation email to customer
    5. Returns success response
    """
    global lead_counter
    
    try:
        # Generate lead ID
        lead_counter += 1
        lead_id = f"LEAD-{lead_counter}"
        
        # Store lead
        lead_data = {
            "lead_id": lead_id,
            "name": request.name,
            "email": request.email,
            "company": request.company,
            "phone": request.phone,
            "service": request.service,
            "message": request.message,
            "budget": request.budget,
            "submitted_at": datetime.utcnow().isoformat(),
            "status": "new",
            "source": "website_contact_form"
        }
        
        leads_db[lead_id] = lead_data
        
        logger.info(f"New lead submitted: {lead_id} - {request.email}")
        
        # Send email notifications
        await send_notification_emails(lead_data, request)
        
        return ContactFormResponse(
            success=True,
            message="Thank you for your interest! We'll contact you within 24 hours.",
            lead_id=lead_id
        )
        
    except Exception as e:
        logger.error(f"Error processing contact form: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to submit form. Please try again or email us directly."
        )


@router.get("/leads")
async def get_all_leads():
    """
    Get all leads (admin endpoint - should be protected).
    """
    return {
        "total_leads": len(leads_db),
        "leads": list(leads_db.values())
    }


@router.get("/leads/{lead_id}")
async def get_lead(lead_id: str):
    """
    Get specific lead details.
    """
    if lead_id not in leads_db:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return leads_db[lead_id]
