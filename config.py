import os

from dotenv import load_dotenv

load_dotenv()

STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET")
CARFAX_SERVICE_URL=os.getenv("CARFAX_SERVICE_URL")

DB_HOST = os.getenv("PAYMENT_DB_HOST")
DB_PORT = os.getenv("PAYMENT_DB_PORT")
DB_USER = os.getenv("PAYMENT_DB_USER")
DB_PASSWORD = os.getenv("PAYMENT_DB_PASS")
DB_NAME = os.getenv("PAYMENT_DB_NAME")