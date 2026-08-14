-- ALIF ERP
-- Phase 12: Achievement Tracking enhancements
-- Safe to run repeatedly.

CREATE TABLE IF NOT EXISTS achievements (
    id BIGSERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    achievement_type VARCHAR(30) NOT NULL,
    event_name VARCHAR(255) NOT NULL,
    position VARCHAR(20),
    assigned_points NUMERIC(10,2),
    title VARCHAR(255) NOT NULL,
    issuing_organization VARCHAR(255),
    achievement_date DATE,
    certificate_number VARCHAR(100),
    verification_value VARCHAR(255),
    certificate_file VARCHAR(500),
    description TEXT,
    points NUMERIC(10,2) NOT NULL DEFAULT 0,
    bonus_points NUMERIC(10,2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    reviewed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Existing deployments may already have this table. The indexes below are harmless
-- in either case and improve institution/student/report lookups.
CREATE INDEX IF NOT EXISTS idx_achievements_institution_student
    ON achievements (institution_id, student_id);

CREATE INDEX IF NOT EXISTS idx_achievements_status
    ON achievements (institution_id, status);

CREATE INDEX IF NOT EXISTS idx_achievements_date
    ON achievements (institution_id, achievement_date);

CREATE INDEX IF NOT EXISTS idx_achievements_reviewed_by
    ON achievements (reviewed_by);

-- Normalize legacy rows before adding constraints.
UPDATE achievements
SET points = 0
WHERE status <> 'Approved' AND COALESCE(points, 0) <> 0;

UPDATE achievements
SET bonus_points = 0
WHERE COALESCE(bonus_points, 0) < 0;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'achievements_type_check'
    ) THEN
        ALTER TABLE achievements
        ADD CONSTRAINT achievements_type_check
        CHECK (achievement_type IN ('Kithab', 'Language', 'Writing', 'Presentation', 'Others'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'achievements_status_check'
    ) THEN
        ALTER TABLE achievements
        ADD CONSTRAINT achievements_status_check
        CHECK (status IN ('Pending', 'Approved', 'Rejected'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'achievements_position_check'
    ) THEN
        ALTER TABLE achievements
        ADD CONSTRAINT achievements_position_check
        CHECK (position IS NULL OR position IN ('First', 'Second', 'Third'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'achievements_points_nonnegative_check'
    ) THEN
        ALTER TABLE achievements
        ADD CONSTRAINT achievements_points_nonnegative_check
        CHECK (COALESCE(points, 0) >= 0 AND COALESCE(bonus_points, 0) >= 0);
    END IF;
END $$;
