from enum import Enum

from pydantic_settings import BaseSettings


class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "payments-service"
    DEBUG: bool = True
    ROOT_PATH: str = ''
    ENVIRONMENT: Environment = Environment.DEVELOPMENT

    @property
    def enable_docs(self) -> bool:
        return self.ENVIRONMENT in [Environment.DEVELOPMENT]

    # database
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "test_db"
    DB_USER: str = "postgres"
    DB_PASS: str = "testpass"

    # rabbitmq
    RABBITMQ_URL: str = 'amqp://guest:guest@localhost:5672/'
    RABBITMQ_EXCHANGE_NAME: str = 'events'
    RABBITMQ_QUEUE_NAME: str = 'payments'

    #rpc
    GRPC_SERVER_PORT: int = 50053

    # stripe
    STRIPE_SECRET_KEY: str = ''
    STRIPE_WEBHOOK_SECRET: str = ''

    class Config:
        env_file = ".env"

settings = Settings()


# DB_HOST = os.getenv("PAYMENT_DB_HOST")
# DB_PORT = os.getenv("PAYMENT_DB_PORT")
# DB_USER = os.getenv("PAYMENT_DB_USER")
# DB_PASSWORD = os.getenv("PAYMENT_DB_PASS")
# DB_NAME = os.getenv("PAYMENT_DB_NAME")