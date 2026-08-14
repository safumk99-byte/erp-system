-- ALIF ERP - Language Skills base schema
CREATE TABLE IF NOT EXISTS language_skill_assessments (
    id BIGSERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    language_name VARCHAR(100) NOT NULL,
    skill_type VARCHAR(20) NOT NULL,
    category VARCHAR(20),
    title VARCHAR(255),
    duration_minutes INTEGER,
    pages INTEGER,
    review TEXT,
    description TEXT,
    points NUMERIC(10,2) NOT NULL DEFAULT 0,
    bonus_points NUMERIC(10,2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    submitted_by INTEGER,
    reviewed_by INTEGER,
    reviewed_at TIMESTAMP,
    rejection_reason TEXT,
    hearing_session_1_minutes INTEGER,
    hearing_session_2_minutes INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT language_base_skill_check CHECK (skill_type IN ('Presentation','Writing','Hearing','Reading')),
    CONSTRAINT language_base_category_check CHECK (category IS NULL OR category IN ('Fiction','Non-Fiction')),
    CONSTRAINT language_base_status_check CHECK (status IN ('Pending','Approved','Rejected')),
    CONSTRAINT language_base_points_check CHECK (points >= 0 AND bonus_points >= 0),
    CONSTRAINT language_base_duration_check CHECK (duration_minutes IS NULL OR duration_minutes > 0),
    CONSTRAINT language_base_pages_check CHECK (pages IS NULL OR pages > 0)
);

CREATE INDEX IF NOT EXISTS idx_language_base_institution_student ON language_skill_assessments(institution_id, student_id);

-- ALIF ERP - Language Skills enhancements
-- Proposal: language-wise tracking; presentation 5 min/5 pts;
-- hearing two separate 5-min sessions + written review/3 pts;
-- writing/reading follow their respective assessment rules.

ALTER TABLE language_skill_assessments
    ADD COLUMN IF NOT EXISTS submitted_by INTEGER;

ALTER TABLE language_skill_assessments
    ADD COLUMN IF NOT EXISTS hearing_session_1_minutes INTEGER;

ALTER TABLE language_skill_assessments
    ADD COLUMN IF NOT EXISTS hearing_session_2_minutes INTEGER;

CREATE INDEX IF NOT EXISTS idx_language_student_language
    ON language_skill_assessments (institution_id, student_id, language_name);

CREATE INDEX IF NOT EXISTS idx_language_status_language
    ON language_skill_assessments (institution_id, status, language_name);

CREATE INDEX IF NOT EXISTS idx_language_submitted_by
    ON language_skill_assessments (submitted_by);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'language_hearing_session_1_positive'
    ) THEN
        ALTER TABLE language_skill_assessments
            ADD CONSTRAINT language_hearing_session_1_positive
            CHECK (hearing_session_1_minutes IS NULL OR hearing_session_1_minutes > 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'language_hearing_session_2_positive'
    ) THEN
        ALTER TABLE language_skill_assessments
            ADD CONSTRAINT language_hearing_session_2_positive
            CHECK (hearing_session_2_minutes IS NULL OR hearing_session_2_minutes > 0);
    END IF;
END $$;
