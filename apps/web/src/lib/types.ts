export type Provider = "mock" | "facebook" | "instagram" | "linkedin" | "whatsapp" | "youtube" | "tiktok" | "x";
export type PostStatus = "draft" | "generated" | "approved" | "scheduled" | "publishing" | "published" | "failed" | "cancelled";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

export interface SocialPost {
  id: string;
  campaign_id: string;
  connection_id: string | null;
  platform: Provider;
  title: string;
  body: string;
  hashtags: string[];
  call_to_action: string;
  visual_idea: string;
  media_url: string;
  provider_payload: Record<string, unknown>;
  status: PostStatus;
  scheduled_for: string | null;
  approved_at: string | null;
  published_at: string | null;
  external_post_id: string;
  external_post_url: string;
  retry_count: number;
  last_error: string;
  created_at: string;
  updated_at: string;
}

export interface Campaign {
  id: string;
  name: string;
  brief: string;
  content_type: string;
  language: string;
  tone: string;
  audience: string;
  objective: string;
  status: string;
  settings: Record<string, unknown>;
  posts: SocialPost[];
  created_at: string;
  updated_at: string;
}

export interface Connection {
  id: string;
  provider: Provider;
  display_name: string;
  external_account_id: string;
  token_expires_at: string | null;
  metadata_json: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Lead {
  id: string;
  phone_number: string;
  student_name: string;
  father_name: string;
  age: string;
  course: string;
  preferred_days: string;
  preferred_time: string;
  country: string;
  status: string;
  details_json: Record<string, unknown>;
  summary: string;
  created_at: string;
  updated_at: string;
}

export interface Summary {
  campaigns: number;
  draft_posts: number;
  scheduled_posts: number;
  published_posts: number;
  failed_posts: number;
  new_leads: number;
  active_connections: number;
}


export interface AuditEvent {
  id: string;
  created_at: string;
  actor_user_id: string | null;
  action: string;
  target_type: string;
  target_id: string;
  metadata_json: Record<string, unknown>;
}
