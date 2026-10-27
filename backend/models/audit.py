from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Index
from backend.database import Base


class AuditLog(Base):
    __tablename__ = "auth_audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_id = Column(String(36), nullable=True, index=True)
    actor_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    target_id = Column(String(36), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_auth_audit_action_time", action, created_at),
    )
