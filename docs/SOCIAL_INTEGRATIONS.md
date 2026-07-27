# Social Integrations

## General connection model

Each connection stores:

• Provider
• Display name
• External account identifier
• Encrypted access token
• Optional encrypted refresh token
• Provider metadata such as Page ID or Organization URN
• Enabled status

The current foundation supports manual secure token connection and provider adapters. OAuth routes are included for the major providers and can be expanded when application review is approved.

## Facebook Page

Required metadata:

```json
{
  "page_id": "PAGE_ID"
}
```

The access token must be a Page access token with the permissions approved for your Meta application.

## Instagram Professional account

Required metadata:

```json
{
  "ig_user_id": "INSTAGRAM_USER_ID",
  "media_type": "IMAGE"
}
```

Instagram publishing requires a public media URL. Text only Instagram publishing is rejected by the adapter.

## WhatsApp Cloud API

Required metadata:

```json
{
  "phone_number_id": "PHONE_NUMBER_ID",
  "business_account_id": "WABA_ID"
}
```

The webhook route is:

```text
/api/v1/webhooks/whatsapp
```

Set the same verification token in Meta and `WHATSAPP_VERIFY_TOKEN`.

## LinkedIn organization

Required metadata:

```json
{
  "author_urn": "urn:li:organization:123456"
}
```

The authenticated member must have a suitable Page role and the application must have organization publishing permission.

## YouTube

Required metadata:

```json
{
  "privacy_status": "private",
  "category_id": "27"
}
```

A post must contain a video media URL. The worker downloads the file and uses a resumable YouTube upload session.

## TikTok

Required metadata:

```json
{
  "privacy_level": "SELF_ONLY",
  "brand_organic_toggle": true
}
```

Video posts use a public video URL. Photo posts use public image URLs stored in the post metadata. Domains may need to be verified with TikTok.

## X

The adapter posts text through the X API. The access token must represent the authorized user and include write permission. API access may require a paid developer plan.

## Provider reviews

Real public publishing can remain limited until each provider approves the application and requested permissions. This is an external platform requirement, not a code issue.
