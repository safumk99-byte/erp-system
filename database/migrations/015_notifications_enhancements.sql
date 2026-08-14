-- ALIF ERP Notification Foundation
-- Creates the canonical notification table used by in-app alerts.

CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    channel VARCHAR(20) NOT NULL DEFAULT 'in_app',
    delivery_status VARCHAR(20) NOT NULL DEFAULT 'delivered',
    scheduled_at TIMESTAMPTZ NULL,
    sent_at TIMESTAMPTZ NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMPTZ NULL,
    related_type VARCHAR(50) NULL,
    related_id BIGINT NULL,
    dedupe_key VARCHAR(255) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT notifications_channel_chk CHECK (channel IN ('in_app','email','sms')),
    CONSTRAINT notifications_delivery_status_chk CHECK (delivery_status IN ('pending','delivered','failed','cancelled'))
);

ALTER TABLE notifications ADD COLUMN IF NOT EXISTS channel VARCHAR(20) NOT NULL DEFAULT 'in_app';
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS delivery_status VARCHAR(20) NOT NULL DEFAULT 'delivered';
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMPTZ NULL;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS sent_at TIMESTAMPTZ NULL;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS related_type VARCHAR(50) NULL;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS related_id BIGINT NULL;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS dedupe_key VARCHAR(255) NULL;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS is_read BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS read_at TIMESTAMPTZ NULL;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_notifications_user_inbox
    ON notifications (institution_id, user_id, is_read, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_notifications_type_created
    ON notifications (institution_id, notification_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_notifications_scheduled
    ON notifications (delivery_status, scheduled_at)
    WHERE scheduled_at IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_notifications_dedupe
    ON notifications (institution_id, user_id, notification_type, dedupe_key)
    WHERE dedupe_key IS NOT NULL;
