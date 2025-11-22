"""
Contact form API endpoints for lead generation.
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, validator
import logging

logger = logging.getLogger(__name__)

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
        
        # TODO: Send email notifications
        # await send_notification_to_sales(lead_data)
        # await send_confirmation_to_customer(request.email, request.name)
        
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
