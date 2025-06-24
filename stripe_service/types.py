from pydantic import BaseModel

class ProductData(BaseModel):
    name: str

class Price(BaseModel):
    currency: str = 'EUR'
    product_data: ProductData
    unit_amount: int


class Product(BaseModel):
    price_data: Price
    quantity: int

class WebhookData(BaseModel):
    payment_intent: str
    amount_total: int
    status: str
    payment_status: str
    currency: str
    checkout_id: str



