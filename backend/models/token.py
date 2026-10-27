from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class EmailVerificationToken(Base):
    __tablename__ = "auth_email_verifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    otp_hash = Column(String(64), nullable=False, index=True)
    attempts = Column(Integer, default=0, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="email_verifications")

    def is_valid(self) -> bool:
        if self.used_at is not None:
            return False
        if datetime.utcnow() > self.expires_at:
            return False
        return True


class PasswordResetToken(Base):
    __tablename__ = "auth_password_resets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="password_resets")

    def is_valid(self) -> bool:
        if self.used_at is not None:
            return False
        if datetime.utcnow() > self.expires_at:
            return False
        return True
