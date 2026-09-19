from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, JSON

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_type = Column(String(20), nullable=False)  # USER, DEVICE, SYSTEM
    actor_id = Column(String(64), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(64), nullable=False, index=True)
    details = Column(JSON, default=dict, nullable=False)

    # Tamper-evident hash chaining
    prev_hash = Column(String(64), nullable=False)
    entry_hash = Column(String(64), nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
