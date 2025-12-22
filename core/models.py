from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Integer, DateTime, Index, ForeignKey, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from config.database import Base
from core.consts import SMSStatus, SMSType


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    api_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    sms_records = relationship("SMS", back_populates="user", lazy="select")

    __table_args__ = (
        Index("idx_users_api_key", "api_key"),
    )


class SMS(Base):
    __tablename__ = "sms"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(String(70), nullable=False)
    sms_type: Mapped[int] = mapped_column(SmallInteger, default=SMSType.REGULAR, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=SMSStatus.PENDING, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user = relationship("User", back_populates="sms_records", lazy="select")

    __table_args__ = (
        Index("idx_sms_user_created", "user_id", "created_at"),
        Index("idx_sms_user_status", "user_id", "status", "created_at"),
        Index("idx_sms_status", "status"),
        Index("idx_sms_created", "created_at"),
        {
            "postgresql_partition_by": "RANGE (created_at)"
        }
    )

    __mapper_args__ = {
        "primary_key": [id, created_at]
    }
