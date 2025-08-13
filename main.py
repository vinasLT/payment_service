import uvicorn
from fastapi import FastAPI

from config import settings
from router.stripe import stripe_router

docs_url = "/docs" if settings.enable_docs else None
redoc_url = "/redoc"  if settings.enable_docs else None
openapi_url = "/openapi.json" if settings.enable_docs else None

app = FastAPI(
    title="Payment Service",
    description="Accept payments from stripe",
    version="0.0.1",
    root_path=settings.ROOT_PATH,
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
)


app.include_router(stripe_router, prefix="/stripe", tags=["Stripe"])

if __name__ == '__main__':
    uvicorn.run(app, host="localhost", port=8002)