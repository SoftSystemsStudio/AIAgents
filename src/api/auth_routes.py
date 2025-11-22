"""
Authentication API Endpoints.

Handles customer signup, login, and token management.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from src.domain.customer import Customer, PlanTier, CustomerStatus
from src.api.auth import (
    create_access_token,
    verify_password,
    get_current_customer,
    TokenResponse,
)
from src.infrastructure.customer_repository import customer_repository

router = APIRouter()


class SignupRequest(BaseModel):
    """Customer signup request"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    name: Optional[str] = None


class LoginRequest(BaseModel):
    """Customer login request"""
    email: EmailStr
    password: str


class CustomerResponse(BaseModel):
    """Customer information response"""
    id: str
    email: str
    name: Optional[str]
    plan_tier: str
    status: str
    is_on_trial: bool
    trial_ends_at: Optional[datetime]
    created_at: datetime


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest):
    """
    Create a new customer account.
    
    Creates customer with:
    - FREE plan tier
    - 14-day trial
    - Hashed password
    - JWT token for immediate login
    
    Returns JWT token for authentication.
    """
    try:
        # Create customer
        customer = customer_repository.create(
            email=request.email,
            password=request.password,
            name=request.name,
            plan_tier=PlanTier.FREE,
        )
        
        # Generate JWT token
        access_token = create_access_token(customer)
        
        # Calculate expiration
        expires_in = 60 * 60 * 24  # 24 hours in seconds
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
            customer={
                "id": str(customer.id),
                "email": customer.email,
                "name": customer.name,
                "plan_tier": customer.plan_tier.value,
                "is_on_trial": customer.is_on_trial(),
            },
        )
    
    except ValueError as e:
        # Email already exists
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login with email and password.
    
    Validates credentials and returns JWT token.
    """
    # Get customer by email
    customer = customer_repository.get_by_email(request.email)
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(request.password, customer.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if account is active
    if customer.status != CustomerStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {customer.status.value.lower()}. Please contact support."
        )
    
    # Generate JWT token
    access_token = create_access_token(customer)
    expires_in = 60 * 60 * 24  # 24 hours
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        customer={
            "id": str(customer.id),
            "email": customer.email,
            "name": customer.name,
            "plan_tier": customer.plan_tier.value,
            "is_on_trial": customer.is_on_trial(),
        },
    )


@router.get("/me", response_model=CustomerResponse)
async def get_current_user(customer: Customer = Depends(get_current_customer)):
    """
    Get current authenticated customer information.
    
    Requires valid JWT token.
    """
    return CustomerResponse(
        id=str(customer.id),
        email=customer.email,
        name=customer.name,
        plan_tier=customer.plan_tier.value,
        status=customer.status.value,
        is_on_trial=customer.is_on_trial(),
        trial_ends_at=customer.trial_ends_at,
        created_at=customer.created_at,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(customer: Customer = Depends(get_current_customer)):
    """
    Refresh JWT token.
    
    Use when token is about to expire.
    Requires current valid token.
    """
    # Generate new token
    access_token = create_access_token(customer)
    expires_in = 60 * 60 * 24  # 24 hours
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        customer={
            "id": str(customer.id),
            "email": customer.email,
            "name": customer.name,
            "plan_tier": customer.plan_tier.value,
            "is_on_trial": customer.is_on_trial(),
        },
    )


@router.post("/logout")
async def logout(customer: Customer = Depends(get_current_customer)):
    """
    Logout (client-side only).
    
    JWT tokens are stateless, so logout is handled client-side
    by deleting the token. This endpoint exists for consistency.
    """
    return {
        "message": "Logged out successfully",
        "customer_id": str(customer.id),
    }
