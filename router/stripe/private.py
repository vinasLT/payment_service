from fastapi import APIRouter, Body, Depends
from pydantic import HttpUrl


from fastapi import HTTPException

from database.crud.payment import PaymentService
from database.schemas.payment import Purposes, PaymentCreate
from dependencies.get_user import User, get_user
from schemas import StripeCheckOutIn, StripeCheckOutOut
from services.stripe_service.service import StripeService

stripe_private_router = APIRouter()




