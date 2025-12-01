import stripe
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, model_validator
from typing import Any, Dict
from .config import settings
from .db import init_db, db

# Set stripe API key dynamically - will be updated in each request
stripe.api_key = settings.stripe_secret_key

router = APIRouter(prefix="/api/payments", tags=["payments"])


class CheckoutSessionRequest(BaseModel):
    amount: int | None = Field(default=None, description="Amount in rupees")
    amount_in_paise: int | None = Field(default=None, description="Amount already converted to paise")
    currency: str = Field(default="inr", min_length=3, max_length=3)
    description: str = Field(default="Order", max_length=200)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_amount(self):
        if self.amount is None and self.amount_in_paise is None:
            raise ValueError("Provide either amount (in rupees) or amount_in_paise (in paise)")
        if self.amount is not None and self.amount < 1:
            raise ValueError("Amount must be at least 1 rupee")
        if self.amount_in_paise is not None and self.amount_in_paise < 1:
            raise ValueError("Amount in paise must be positive")
        return self

    def to_paise(self) -> int:
        if self.amount_in_paise is not None:
            return self.amount_in_paise
        return self.amount * 100  # type: ignore[operator]

# create checkout session
@router.post("/create-checkout-session")
async def create_checkout_session(payload: CheckoutSessionRequest):
    """
    payload must include: amount (in rupees) or amount_in_paise,
    and optionally: currency, description, metadata
    """
    if not settings.stripe_secret_key or settings.stripe_secret_key == "sk_test_YOUR_SECRET_KEY_HERE":
        raise HTTPException(
            status_code=400,
            detail="Stripe secret key is not configured. Please set STRIPE_SECRET_KEY in your .env file. Get your keys from https://dashboard.stripe.com/test/apikeys",
        )

    # Ensure stripe.api_key is set to current value (in case server wasn't restarted)
    stripe.api_key = settings.stripe_secret_key

    try:
        amount_paise = payload.to_paise()

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": payload.currency,
                    "product_data": {
                        "name": payload.description,
                    },
                    "unit_amount": amount_paise,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{settings.frontend_url}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.frontend_url}/cancel",
            metadata=payload.metadata,
        )
        # Optionally store session in DB
        if db is None:
            init_db()
        if db:
            await db.orders.insert_one({
                "session_id": session.id,
                "amount": amount_paise,
                "currency": payload.currency,
                "status": "created",
                "created": session.created,
                "metadata": payload.metadata
            })
        return {"sessionId": session.id, "checkout_url": session.url}
    except stripe.error.StripeError as exc:
        raise HTTPException(status_code=502, detail=exc.user_message or str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

# webhook endpoint for Stripe to notify events
@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not settings.stripe_webhook_secret:
        # If webhook secret not configured, try to process without verification (not recommended)
        # But better to return error and instruct to set
        return JSONResponse({"error": "Webhook secret not set on server"}, status_code=500)

    # Ensure stripe.api_key is set to current value
    stripe.api_key = settings.stripe_secret_key

    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=sig_header, secret=settings.stripe_webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        return JSONResponse({"error": "Invalid payload"}, status_code=400)
    except stripe.error.SignatureVerificationError as e:
        return JSONResponse({"error": "Invalid signature"}, status_code=400)

    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        # Fulfill the purchase: mark order paid in DB
        if db is None:
            init_db()
        if db:
            await db.orders.update_one({"session_id": session["id"]}, {"$set": {"status": "paid", "payment_status": session.get("payment_status")}})
        # You can also capture analytics, send emails etc.
    # you can handle other events: payment_intent.succeeded, charge.failed, etc.

    return JSONResponse({"status": "success"})
