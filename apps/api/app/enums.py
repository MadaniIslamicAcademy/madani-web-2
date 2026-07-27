from enum import StrEnum


class UserRole(StrEnum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    EDITOR = "editor"
    REVIEWER = "reviewer"


class CampaignStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class PostStatus(StrEnum):
    DRAFT = "draft"
    GENERATED = "generated"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SocialProvider(StrEnum):
    MOCK = "mock"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    WHATSAPP = "whatsapp"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    X = "x"


class AttemptStatus(StrEnum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class LeadStatus(StrEnum):
    NEW = "new"
    COLLECTING = "collecting"
    READY_FOR_TEAM = "ready_for_team"
    CONTACTED = "contacted"
    ENROLLED = "enrolled"
    CLOSED = "closed"
