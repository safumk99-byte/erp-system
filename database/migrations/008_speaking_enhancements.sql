-- ALIF ERP - Speaking Skill base schema
CREATE TABLE IF NOT EXISTS speaking_submissions (
    id BIGSERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    presentation_date DATE,
    duration_minutes INTEGER NOT NULL,
    description TEXT,
    points NUMERIC(10,2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    submitted_by INTEGER,
    reviewed_by INTEGER,
    reviewed_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT speaking_base_status_check CHECK (status IN ('Pending','Approved','Rejected')),
    CONSTRAINT speaking_base_duration_check CHECK (duration_minutes > 0),
    CONSTRAINT speaking_base_points_check CHECK (points >= 0)
);

CREATE INDEX IF NOT EXISTS idx_speaking_base_institution_student ON speaking_submissions(institution_id, student_id);

-- =========================================
-- Speaking Skill enhancements
-- Proposal: public presentation >= 5 minutes -> 5 points after approval
-- =========================================

ALTER TABLE speaking_submissions
    ADD COLUMN IF NOT EXISTS submitted_by INTEGER;

CREATE INDEX IF NOT EXISTS idx_speaking_institution_student
    ON speaking_submissions (institution_id, student_id);

CREATE INDEX IF NOT EXISTS idx_speaking_status
    ON speaking_submissions (institution_id, status);

CREATE INDEX IF NOT EXISTS idx_speaking_reviewed_by
    ON speaking_submissions (reviewed_by);

-- Keep points zero until an authorized reviewer approves.
UPDATE speaking_submissions
SET points = 0
WHERE status <> 'Approved';

-- Approved records under the proposal must have the minimum duration.
UPDATE speaking_submissions
SET points = 5
WHERE status = 'Approved' AND duration_minutes >= 5;

UPDATE speaking_submissions
SET points = 0, status = 'Pending'
WHERE status = 'Approved' AND duration_minutes < 5;
