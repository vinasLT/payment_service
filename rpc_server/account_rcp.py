import os
import sys

import grpc

from core.logger import logger
from database.crud.plan import PlanService
from database.crud.transaction import TransactionService
from database.crud.user_account import UserAccountService
from database.db.session import get_db_context
from database.models.plan import Plan
from database.models.transaction import TransactionType
from database.schemas.transaction import TransactionCreate
from database.schemas.user_account import UserAccountUpdate, UserAccountCreate

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gen', 'python'))
from rpc_server.gen.python.payment.v1 import stripe_pb2, stripe_pb2_grpc


class AccountRcp(stripe_pb2_grpc.PaymentServiceServicer):
    _PROTO_TO_MODEL_TRANSACTION_TYPE = {
        stripe_pb2.TransactionType.TRANSACTION_TYPE_PLAN_PURCHASE: TransactionType.PLAN_PURCHASE,
        stripe_pb2.TransactionType.TRANSACTION_TYPE_BID_PLACEMENT: TransactionType.BID_PLACEMENT,
        stripe_pb2.TransactionType.TRANSACTION_TYPE_ADJUSTMENT: TransactionType.ADJUSTMENT,
    }
    _MODEL_TO_PROTO_TRANSACTION_TYPE = {
        value: key for key, value in _PROTO_TO_MODEL_TRANSACTION_TYPE.items()
    }

    async def CreateNewTransaction(
        self, request: stripe_pb2.CreateNewTransactionRequest, context
    ):
        logger.debug("Received create_new_transaction rpc request")

        if not request.user_uuid:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("user_uuid is required")
            return stripe_pb2.CreateNewTransactionResponse()

        transaction_type = self._PROTO_TO_MODEL_TRANSACTION_TYPE.get(
            request.transaction_type
        )
        if not transaction_type:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("transaction_type is invalid or unspecified")
            return stripe_pb2.CreateNewTransactionResponse()

        plan_id = request.plan_id if request.HasField("plan_id") else None

        try:
            async with get_db_context() as db:
                account_service = UserAccountService(db)
                transaction_service = TransactionService(db)
                plan_service = PlanService(db)

                account = await account_service.get_by_user_uuid(request.user_uuid)

                plan = None
                if plan_id is not None:
                    plan = await plan_service.get(plan_id)
                    if not plan:
                        context.set_code(grpc.StatusCode.NOT_FOUND)
                        context.set_details("Plan not found")
                        return stripe_pb2.CreateNewTransactionResponse()

                if transaction_type == TransactionType.PLAN_PURCHASE and plan is None:
                    context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                    context.set_details("PLAN_PURCHASE transactions require plan_id")
                    return stripe_pb2.CreateNewTransactionResponse()

                transaction = await transaction_service.create(
                    TransactionCreate(
                        user_account_id=account.id,
                        plan_id=plan.id if plan else None,
                        transaction_type=transaction_type,
                        amount=request.amount,
                    )
                )

                account = await self._apply_account_updates(
                    account_service,
                    account,
                    plan_id=plan.id if plan else None,
                    balance_delta=request.amount,
                )

                response = stripe_pb2.CreateNewTransactionResponse(
                    user_account_id=account.id,
                    transaction_type=self._MODEL_TO_PROTO_TRANSACTION_TYPE[
                        transaction.transaction_type
                    ],
                    amount=transaction.amount,
                )
                if transaction.plan_id is not None:
                    response.plan_id = transaction.plan_id
                return response
        except Exception as exc:
            logger.error(f"Error while processing CreateNewTransaction: {exc}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal error")
            return stripe_pb2.CreateNewTransactionResponse()

    async def GetUserAccount(
        self, request: stripe_pb2.GetUserAccountRequest, context
    ):
        logger.debug("Received get_user_account rpc request")

        if not request.user_uuid:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("user_uuid is required")
            return stripe_pb2.GetUserAccountResponse()

        try:
            async with get_db_context() as db:
                account_service = UserAccountService(db)
                account = await account_service.get_by_user_uuid(request.user_uuid)
                if not account:
                    account = await account_service.create(
                        UserAccountCreate(user_uuid=request.user_uuid)
                    )

                response = stripe_pb2.GetUserAccountResponse(
                    user_uuid=account.user_uuid,
                    balance=account.balance,
                )

                plan_proto = self._plan_to_proto(account.plan) if account.plan else None
                if plan_proto:
                    response.plan.CopyFrom(plan_proto)
                return response
        except Exception as exc:
            logger.error(f"Error while processing GetUserAccount: {exc}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal error")
            return stripe_pb2.GetUserAccountResponse()

    @staticmethod
    async def _apply_account_updates(
        account_service: UserAccountService,
        account,
        *,
        plan_id: int | None,
        balance_delta: int,
    ):
        update_data = {}
        if plan_id is not None and account.plan_id != plan_id:
            update_data["plan_id"] = plan_id
        if balance_delta != 0:
            update_data["balance"] = account.balance + balance_delta

        if not update_data:
            return account

        updated_account = await account_service.update(
            account.id,
            UserAccountUpdate(**update_data),
        )
        return updated_account or account

    @staticmethod
    def _plan_to_proto(plan: Plan) -> stripe_pb2.Plan:
        return stripe_pb2.Plan(
            name=plan.name or "",
            description=plan.description or "",
            max_bid_one_time=int(plan.max_bid_one_time),
            bid_power=int(plan.bid_power),
            price=int(plan.price),
        )
