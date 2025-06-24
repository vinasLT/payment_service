import os

from dotenv import load_dotenv

load_dotenv()

STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET")
CARFAX_SERVICE_URL=os.getenv("CARFAX_SERVICE_URL")