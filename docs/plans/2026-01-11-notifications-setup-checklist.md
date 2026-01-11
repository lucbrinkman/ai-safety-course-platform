# Notifications Setup Checklist

Once you have a domain, follow these steps to enable the notification system.

## 1. SendGrid Account Setup

### Create Account
1. Go to https://sendgrid.com and create a free account
2. Free tier: 100 emails/day (enough for development, upgrade later)

### Verify Sender Identity

**Option A: Domain Authentication (Recommended for production)**
1. SendGrid Dashboard → Settings → Sender Authentication
2. Click "Authenticate Your Domain"
3. Add these DNS records to your domain:
   - 3 CNAME records for DKIM
   - 1 CNAME record for branded links (optional)
4. Wait for verification (can take up to 48 hours)
5. Use any `@yourdomain.com` address as sender

**Option B: Single Sender Verification (Quick start)**
1. SendGrid Dashboard → Settings → Sender Authentication
2. Click "Verify a Single Sender"
3. Enter an email address you control
4. Click verification link sent to that email
5. Can only send from that specific address

### Create API Key
1. SendGrid Dashboard → Settings → API Keys
2. Click "Create API Key"
3. Name: `ai-safety-course-notifications`
4. Permissions: "Restricted Access" → enable only "Mail Send"
5. Copy the key (shown only once)

## 2. Environment Variables

Add to `.env.local` (development) and Railway (production):

```bash
# SendGrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxx
FROM_EMAIL=notifications@yourdomain.com

# Discord (get from Discord Developer Portal or server settings)
DISCORD_SERVER_ID=123456789012345678
```

### Finding Your Discord Server ID
1. Enable Developer Mode: User Settings → App Settings → Advanced → Developer Mode
2. Right-click your server icon → "Copy Server ID"

## 3. Database Setup

APScheduler creates its table automatically on first run. If you prefer explicit migration:

```sql
-- APScheduler will create this, but here's the schema for reference
CREATE TABLE apscheduler_jobs (
    id VARCHAR(191) NOT NULL,
    next_run_time FLOAT,
    job_state BYTEA NOT NULL,
    PRIMARY KEY (id)
);
CREATE INDEX ix_apscheduler_jobs_next_run_time ON apscheduler_jobs (next_run_time);
```

## 4. Test the Setup

### Test Email Sending
```python
# Run in Python shell
from core.notifications.channels.email import send_email

result = send_email(
    to_email="your-email@example.com",
    subject="Test from AI Safety Course",
    body="If you see this, SendGrid is working!",
)
print(f"Email sent: {result}")
```

### Test Full Notification
```python
# Requires a user in the database
from core.notifications import notify_welcome

result = await notify_welcome(user_id=1)
print(f"Notification result: {result}")
```

## 5. Monitoring

### SendGrid Dashboard
- Activity Feed: See sent emails, opens, clicks
- Suppressions: Bounces, unsubscribes, spam reports
- Stats: Delivery rates, engagement

### Application Logs
The notification system prints warnings for:
- Missing API keys
- Failed sends
- Missing user data

## 6. Production Considerations

### Upgrade SendGrid Plan
- Free: 100 emails/day
- Essentials ($20/mo): 50,000 emails/month
- Upgrade when you exceed free tier or need better deliverability

### Warm Up Your Domain
New domains have no reputation. SendGrid recommends:
- Week 1: 50 emails/day
- Week 2: 100 emails/day
- Week 3: 500 emails/day
- Gradually increase

### Set Up Bounce Handling
SendGrid can POST bounce/complaint events to a webhook. Consider adding an endpoint to handle:
- Hard bounces → mark email as invalid
- Spam complaints → disable email notifications for user

## Quick Reference

| Variable | Example | Where to Get |
|----------|---------|--------------|
| `SENDGRID_API_KEY` | `SG.xxx...` | SendGrid → API Keys |
| `FROM_EMAIL` | `notifications@yourdomain.com` | Must be verified in SendGrid |
| `DISCORD_SERVER_ID` | `123456789012345678` | Right-click server → Copy ID |
