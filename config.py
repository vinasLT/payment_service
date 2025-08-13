from enum import Enum

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"

class Settings(BaseSettings):
    #Application
    APP_NAME: str = "payment-service"
    DEBUG: bool = True
    ROOT_PATH: str = ''
    ENVIRONMENT: Environment = Environment.DEVELOPMENT

    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    CARFAX_SERVICE_URL: str

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "test_db"
    DB_USER: str = "postgres"
    DB_PASS: str = "testpass"

settings = Settings()