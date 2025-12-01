#!/usr/bin/env python3
"""Helper script to check if Stripe configuration is set up correctly."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings

print("=" * 60)
print("Stripe Configuration Check")
print("=" * 60)

# Check secret key
secret_key = settings.stripe_secret_key
if not secret_key or secret_key == "sk_test_YOUR_SECRET_KEY_HERE":
    print("❌ STRIPE_SECRET_KEY: NOT CONFIGURED")
    print("   Please update .env file with your actual Stripe secret key")
    print("   Get it from: https://dashboard.stripe.com/test/apikeys")
    sys.exit(1)
elif secret_key.startswith("sk_test_"):
    print(f"✅ STRIPE_SECRET_KEY: Configured ({secret_key[:20]}...)")
else:
    print(f"⚠️  STRIPE_SECRET_KEY: Set but format looks unusual ({secret_key[:20]}...)")

# Check publishable key
pub_key = settings.stripe_publishable_key
if not pub_key or pub_key == "pk_test_YOUR_PUBLISHABLE_KEY_HERE":
    print("⚠️  STRIPE_PUBLISHABLE_KEY: Not configured (optional for backend)")
else:
    print(f"✅ STRIPE_PUBLISHABLE_KEY: Configured ({pub_key[:20]}...)")

# Check URLs
print(f"✅ BASE_URL: {settings.base_url}")
print(f"✅ FRONTEND_URL: {settings.frontend_url}")

print("=" * 60)
print("✅ Configuration looks good! You can start the server now.")
print("=" * 60)

