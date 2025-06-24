from pydantic import BaseModel, HttpUrl


class StripeCheckOutIn(BaseModel):
    source: str
    external_user_id: str
    purpose: str
    purpose_external_id: int
    success_link: HttpUrl
    cancel_link: HttpUrl



class StripeCheckOutOut(BaseModel):
    link: HttpUrl

