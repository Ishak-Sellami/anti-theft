from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, JSON

from app.db.base import Base


class RecoveryPolicyModel(Base):
    __tablename__ = "recovery_policies"

    id = Column(String(64), primary_key=True)  # e.g., pol_stolen_default_v1, pol_normal_default_v1
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)

    policy_json = Column(JSON, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
