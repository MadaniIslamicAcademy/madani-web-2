from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.enums import (
    AttemptStatus,
    CampaignStatus,
    LeadStatus,
    PostStatus,
    SocialProvider,
    UserRole,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def uuid_string() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.ADMIN)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Campaign(TimestampMixin, Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    name: Mapped[str] = mapped_column(String(200), index=True)
    brief: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(80), default="Course Promotion")
    language: Mapped[str] = mapped_column(String(40), default="English")
    tone: Mapped[str] = mapped_column(String(80), default="Warm Islamic")
    audience: Mapped[str] = mapped_column(String(120), default="Parents and Students")
    objective: Mapped[str] = mapped_column(String(120), default="Get enquiries")
    status: Mapped[CampaignStatus] = mapped_column(Enum(CampaignStatus), default=CampaignStatus.DRAFT)
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"))

    posts: Mapped[list[SocialPost]] = relationship(back_populates="campaign", cascade="all, delete-orphan")


class SocialConnection(TimestampMixin, Base):
    __tablename__ = "social_connections"
    __table_args__ = (UniqueConstraint("provider", "external_account_id", name="uq_provider_account"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    provider: Mapped[SocialProvider] = mapped_column(Enum(SocialProvider), index=True)
    display_name: Mapped[str] = mapped_column(String(160))
    external_account_id: Mapped[str] = mapped_column(String(255))
    access_token_encrypted: Mapped[str] = mapped_column(Text, default="")
    refresh_token_encrypted: Mapped[str] = mapped_column(Text, default="")
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    connected_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"))


class SocialPost(TimestampMixin, Base):
    __tablename__ = "social_posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), index=True)
    connection_id: Mapped[str | None] = mapped_column(ForeignKey("social_connections.id"), nullable=True)
    platform: Mapped[SocialProvider] = mapped_column(Enum(SocialProvider), index=True)
    title: Mapped[str] = mapped_column(String(500), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    hashtags: Mapped[list[str]] = mapped_column(JSON, default=list)
    call_to_action: Mapped[str] = mapped_column(Text, default="")
    visual_idea: Mapped[str] = mapped_column(Text, default="")
    media_url: Mapped[str] = mapped_column(Text, default="")
    provider_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[PostStatus] = mapped_column(Enum(PostStatus), default=PostStatus.DRAFT, index=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_post_id: Mapped[str] = mapped_column(String(500), default="")
    external_post_url: Mapped[str] = mapped_column(Text, default="")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str] = mapped_column(Text, default="")

    campaign: Mapped[Campaign] = relationship(back_populates="posts")
    connection: Mapped[SocialConnection | None] = relationship()
    attempts: Mapped[list[PublishAttempt]] = relationship(back_populates="post", cascade="all, delete-orphan")


class PublishAttempt(TimestampMixin, Base):
    __tablename__ = "publish_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    post_id: Mapped[str] = mapped_column(ForeignKey("social_posts.id"), index=True)
    attempt_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[AttemptStatus] = mapped_column(Enum(AttemptStatus))
    provider_response: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error_message: Mapped[str] = mapped_column(Text, default="")

    post: Mapped[SocialPost] = relationship(back_populates="attempts")


class AdmissionLead(TimestampMixin, Base):
    __tablename__ = "admission_leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    whatsapp_user_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(40), index=True)
    student_name: Mapped[str] = mapped_column(String(160), default="")
    father_name: Mapped[str] = mapped_column(String(160), default="")
    age: Mapped[str] = mapped_column(String(40), default="")
    course: Mapped[str] = mapped_column(String(160), default="")
    preferred_days: Mapped[str] = mapped_column(String(160), default="")
    preferred_time: Mapped[str] = mapped_column(String(160), default="")
    country: Mapped[str] = mapped_column(String(100), default="")
    status: Mapped[LeadStatus] = mapped_column(Enum(LeadStatus), default=LeadStatus.NEW, index=True)
    details_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    summary: Mapped[str] = mapped_column(Text, default="")
    assigned_to_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class AdmissionMessage(TimestampMixin, Base):
    __tablename__ = "admission_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    lead_id: Mapped[str] = mapped_column(ForeignKey("admission_leads.id"), index=True)
    direction: Mapped[str] = mapped_column(String(20))
    message_id: Mapped[str] = mapped_column(String(255), default="")
    text: Mapped[str] = mapped_column(Text)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(160), index=True)
    target_type: Mapped[str] = mapped_column(String(80))
    target_id: Mapped[str] = mapped_column(String(80))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
