from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Integer, Index
from sqlalchemy.orm import relationship
from backend.database import Base


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class UserStatus(str, Enum):
    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    DISABLED = "disabled"


class User(Base):
    __tablename__ = "auth_users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default=UserRole.USER.value)
    status = Column(String(50), nullable=False, default=UserStatus.PENDING_VERIFICATION.value)
    
    # Metadata profil tambahan
    institution = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=True)

    # Tracking & Keamanan
    email_verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)

    # Relasi
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    email_verifications = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_auth_users_email_lower", email),
        Index("ix_auth_users_username_lower", username),
    )

    def is_locked(self) -> bool:
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
