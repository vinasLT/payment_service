from datetime import datetime, UTC
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models import Base

if TYPE_CHECKING:
    from database.models.plan import Plan
    from database.models.user_account import UserAccount


class TransactionType(str, Enum):
    PLAN_PURCHASE = "PLAN_PURCHASE"
    BID_PLACEMENT = "BID_PLACEMENT"
    ADJUSTMENT = "ADJUSTMENT"


class Transaction(Base):
    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_account_id: Mapped[int] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("plan.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    transaction_type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType),
        nullable=False,
    )

    amount: Mapped[int] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user_account: Mapped["UserAccount"] = relationship(
        back_populates="transactions",
    )
    plan: Mapped["Plan | None"] = relationship(
        back_populates="transactions",
    )

    __table_args__ = (
        Index(
            "ix_transaction_account_type",
            "user_account_id",
            "transaction_type",
        ),
    )
