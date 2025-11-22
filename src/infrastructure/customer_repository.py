"""
Customer Repository - Data access for customer entities.

Handles CRUD operations for customers in the database.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from dataclasses import asdict

from src.domain.customer import Customer, PlanTier, CustomerStatus, SubscriptionStatus
from src.api.auth import hash_password


class CustomerRepository:
    """
    Repository for customer data access.
    
    In production, this would use SQLAlchemy with PostgreSQL.
    For now, uses in-memory storage for development.
    """
    
    def __init__(self):
        # In-memory storage: {customer_id: customer}
        self._customers_by_id: dict[UUID, Customer] = {}
        # Index by email for login lookups
        self._customers_by_email: dict[str, Customer] = {}
    
    def create(
        self,
        email: str,
        password: str,
        name: Optional[str] = None,
        plan_tier: PlanTier = PlanTier.FREE,
    ) -> Customer:
        """
        Create a new customer.
        
        Args:
            email: Customer email (must be unique)
            password: Plain text password (will be hashed)
            name: Customer name (optional)
            plan_tier: Initial plan tier (defaults to FREE with trial)
            
        Returns:
            Created customer
            
        Raises:
            ValueError: If email already exists
        """
        # Check if email already exists
        if email in self._customers_by_email:
            raise ValueError(f"Customer with email {email} already exists")
        
        # Create customer with 14-day trial
        customer = Customer.create(
            email=email,
            password_hash=hash_password(password),
            name=name,
            plan_tier=plan_tier,
        )
        
        # Store in both indexes
        self._customers_by_id[customer.id] = customer
        self._customers_by_email[email] = customer
        
        return customer
    
    def get_by_id(self, customer_id: UUID) -> Optional[Customer]:
        """
        Get customer by ID.
        
        Args:
            customer_id: Customer UUID
            
        Returns:
            Customer if found, None otherwise
        """
        return self._customers_by_id.get(customer_id)
    
    def get_by_email(self, email: str) -> Optional[Customer]:
        """
        Get customer by email (for login).
        
        Args:
            email: Customer email
            
        Returns:
            Customer if found, None otherwise
        """
        return self._customers_by_email.get(email)
    
    def update(self, customer: Customer) -> Customer:
        """
        Update existing customer.
        
        Args:
            customer: Customer with updated fields
            
        Returns:
            Updated customer
            
        Raises:
            ValueError: If customer doesn't exist
        """
        if customer.id not in self._customers_by_id:
            raise ValueError(f"Customer {customer.id} not found")
        
        # Update both indexes
        old_customer = self._customers_by_id[customer.id]
        
        # If email changed, update email index
        if old_customer.email != customer.email:
            del self._customers_by_email[old_customer.email]
            self._customers_by_email[customer.email] = customer
        
        self._customers_by_id[customer.id] = customer
        
        return customer
    
    def delete(self, customer_id: UUID) -> bool:
        """
        Delete customer (soft delete - sets status to CANCELLED).
        
        Args:
            customer_id: Customer UUID
            
        Returns:
            True if deleted, False if not found
        """
        customer = self.get_by_id(customer_id)
        if not customer:
            return False
        
        # Soft delete - keep data but mark as cancelled
        customer.status = CustomerStatus.CANCELLED
        customer.cancelled_at = datetime.utcnow()
        self.update(customer)
        
        return True
    
    def list_all(
        self,
        status: Optional[CustomerStatus] = None,
        plan_tier: Optional[PlanTier] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Customer]:
        """
        List customers with optional filters.
        
        Args:
            status: Filter by status (optional)
            plan_tier: Filter by plan tier (optional)
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of customers
        """
        customers = list(self._customers_by_id.values())
        
        # Apply filters
        if status:
            customers = [c for c in customers if c.status == status]
        
        if plan_tier:
            customers = [c for c in customers if c.plan_tier == plan_tier]
        
        # Apply pagination
        return customers[offset:offset + limit]
    
    def count(
        self,
        status: Optional[CustomerStatus] = None,
        plan_tier: Optional[PlanTier] = None,
    ) -> int:
        """
        Count customers with optional filters.
        
        Args:
            status: Filter by status (optional)
            plan_tier: Filter by plan tier (optional)
            
        Returns:
            Number of customers matching filters
        """
        customers = list(self._customers_by_id.values())
        
        if status:
            customers = [c for c in customers if c.status == status]
        
        if plan_tier:
            customers = [c for c in customers if c.plan_tier == plan_tier]
        
        return len(customers)
    
    def upgrade_plan(
        self,
        customer_id: UUID,
        new_plan: PlanTier,
        stripe_customer_id: Optional[str] = None,
        stripe_subscription_id: Optional[str] = None,
    ) -> Customer:
        """
        Upgrade customer to a new plan.
        
        Args:
            customer_id: Customer UUID
            new_plan: New plan tier
            stripe_customer_id: Stripe customer ID (optional)
            stripe_subscription_id: Stripe subscription ID (optional)
            
        Returns:
            Updated customer
            
        Raises:
            ValueError: If customer not found
        """
        customer = self.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        customer.plan_tier = new_plan
        customer.subscription_status = SubscriptionStatus.ACTIVE
        
        if stripe_customer_id:
            customer.stripe_customer_id = stripe_customer_id
        
        if stripe_subscription_id:
            customer.stripe_subscription_id = stripe_subscription_id
        
        return self.update(customer)
    
    def suspend(self, customer_id: UUID, reason: Optional[str] = None) -> Customer:
        """
        Suspend customer account.
        
        Args:
            customer_id: Customer UUID
            reason: Reason for suspension (optional)
            
        Returns:
            Updated customer
            
        Raises:
            ValueError: If customer not found
        """
        customer = self.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        customer.status = CustomerStatus.SUSPENDED
        
        return self.update(customer)
    
    def reactivate(self, customer_id: UUID) -> Customer:
        """
        Reactivate suspended customer.
        
        Args:
            customer_id: Customer UUID
            
        Returns:
            Updated customer
            
        Raises:
            ValueError: If customer not found
        """
        customer = self.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        customer.status = CustomerStatus.ACTIVE
        
        return self.update(customer)
    
    def get_trial_expiring_soon(self, days: int = 3) -> List[Customer]:
        """
        Get customers whose trial is expiring soon.
        
        Useful for sending reminder emails.
        
        Args:
            days: Number of days before expiration
            
        Returns:
            List of customers with trials expiring soon
        """
        cutoff = datetime.utcnow() + timedelta(days=days)
        
        expiring = []
        for customer in self._customers_by_id.values():
            if (customer.is_on_trial() and 
                customer.trial_ends_at and 
                customer.trial_ends_at <= cutoff):
                expiring.append(customer)
        
        return expiring
    
    def get_payment_failed(self) -> List[Customer]:
        """
        Get customers with failed payments.
        
        Returns:
            List of customers with payment issues
        """
        return [
            c for c in self._customers_by_id.values()
            if c.subscription_status == SubscriptionStatus.PAST_DUE
        ]
    
    def bulk_create(self, customers: List[dict]) -> List[Customer]:
        """
        Bulk create customers (for testing/seeding).
        
        Args:
            customers: List of customer dictionaries
            
        Returns:
            List of created customers
        """
        created = []
        for customer_data in customers:
            try:
                customer = self.create(
                    email=customer_data['email'],
                    password=customer_data['password'],
                    name=customer_data.get('name'),
                    plan_tier=customer_data.get('plan_tier', PlanTier.FREE),
                )
                created.append(customer)
            except ValueError:
                # Skip duplicates
                continue
        
        return created


# Global instance (in production, inject via dependency injection)
customer_repository = CustomerRepository()
