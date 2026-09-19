from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime

from app.db.base import Base


class UsedNonce(Base):
    __tablename__ = "used_nonces"

    nonce = Column(String(64), primary_key=True)
    device_id = Column(String(64), nullable=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
