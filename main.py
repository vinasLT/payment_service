import uvicorn
from fastapi import FastAPI
from router.stripe import stripe_router


app = FastAPI()

app.include_router(stripe_router, prefix="/stripe", tags=["Stripe"])

if __name__ == '__main__':
    uvicorn.run(app, host="localhost", port=8002)