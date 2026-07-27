from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.enums import CampaignStatus, LeadStatus, PostStatus, SocialProvider, UserRole


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)


class UserRead(ORMModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool


class AuthResponse(BaseModel):
    user: UserRead
    csrf_token: str


class CampaignCreate(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    brief: str = Field(min_length=5)
    content_type: str = "Course Promotion"
    language: str = "English"
    tone: str = "Warm Islamic"
    audience: str = "Parents and Students"
    objective: str = "Get enquiries"
    platforms: list[SocialProvider] = Field(min_length=1)
    settings: dict[str, Any] = Field(default_factory=dict)


class CampaignUpdate(BaseModel):
    name: str | None = None
    brief: str | None = None
    status: CampaignStatus | None = None
    content_type: str | None = None
    language: str | None = None
    tone: str | None = None
    audience: str | None = None
    objective: str | None = None
    settings: dict[str, Any] | None = None


class PostRead(ORMModel):
    id: str
    campaign_id: str
    connection_id: str | None
    platform: SocialProvider
    title: str
    body: str
    hashtags: list[str]
    call_to_action: str
    visual_idea: str
    media_url: str
    provider_payload: dict[str, Any]
    status: PostStatus
    scheduled_for: datetime | None
    approved_at: datetime | None
    published_at: datetime | None
    external_post_id: str
    external_post_url: str
    retry_count: int
    last_error: str
    created_at: datetime
    updated_at: datetime


class CampaignRead(ORMModel):
    id: str
    name: str
    brief: str
    content_type: str
    language: str
    tone: str
    audience: str
    objective: str
    status: CampaignStatus
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    posts: list[PostRead] = Field(default_factory=list)


class PostUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    hashtags: list[str] | None = None
    call_to_action: str | None = None
    visual_idea: str | None = None
    media_url: str | None = None
    provider_payload: dict[str, Any] | None = None
    connection_id: str | None = None


class ScheduleRequest(BaseModel):
    scheduled_for: datetime


class ConnectionCreate(BaseModel):
    provider: SocialProvider
    display_name: str = Field(min_length=2, max_length=160)
    external_account_id: str = Field(min_length=1, max_length=255)
    access_token: str = ""
    refresh_token: str = ""
    token_expires_at: datetime | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class ConnectionUpdate(BaseModel):
    display_name: str | None = None
    external_account_id: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    token_expires_at: datetime | None = None
    metadata_json: dict[str, Any] | None = None
    is_active: bool | None = None


class ConnectionRead(ORMModel):
    id: str
    provider: SocialProvider
    display_name: str
    external_account_id: str
    token_expires_at: datetime | None
    metadata_json: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LeadRead(ORMModel):
    id: str
    phone_number: str
    student_name: str
    father_name: str
    age: str
    course: str
    preferred_days: str
    preferred_time: str
    country: str
    status: LeadStatus
    details_json: dict[str, Any]
    summary: str
    created_at: datetime
    updated_at: datetime


class LeadUpdate(BaseModel):
    status: LeadStatus | None = None
    assigned_to_id: str | None = None
    details_json: dict[str, Any] | None = None


class AuditRead(ORMModel):
    id: str
    created_at: datetime
    actor_user_id: str | None
    action: str
    target_type: str
    target_id: str
    metadata_json: dict[str, Any]


class DashboardSummary(BaseModel):
    campaigns: int
    draft_posts: int
    scheduled_posts: int
    published_posts: int
    failed_posts: int
    new_leads: int
    active_connections: int
