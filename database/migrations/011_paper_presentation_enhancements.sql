-- ALIF ERP - Paper Presentation base schema
CREATE TABLE IF NOT EXISTS paper_presentations (
    id BIGSERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    presentation_level VARCHAR(20) NOT NULL,
    affiliated_institution VARCHAR(255),
    certificate_file VARCHAR(500),
    verification_value VARCHAR(255),
    description TEXT,
    submitted_by INTEGER,
    points NUMERIC(10,2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    reviewed_by INTEGER,
    reviewed_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT paper_base_level_check CHECK (presentation_level IN ('State','National','International','Others')),
    CONSTRAINT paper_base_status_check CHECK (status IN ('Pending','Approved','Rejected')),
    CONSTRAINT paper_base_points_check CHECK (points >= 0)
);

CREATE INDEX IF NOT EXISTS idx_paper_base_institution_student ON paper_presentations(institution_id, student_id);

-- ALIF ERP: Paper Presentation enhancements
-- Adds submission auditability and integrity constraints.

ALTER TABLE paper_presentations
    ADD COLUMN IF NOT EXISTS submitted_by INTEGER;

CREATE INDEX IF NOT EXISTS idx_paper_presentations_institution_student
    ON paper_presentations (institution_id, student_id);

CREATE INDEX IF NOT EXISTS idx_paper_presentations_status
    ON paper_presentations (institution_id, status);

CREATE INDEX IF NOT EXISTS idx_paper_presentations_level
    ON paper_presentations (institution_id, presentation_level);

ALTER TABLE paper_presentations
    DROP CONSTRAINT IF EXISTS paper_presentations_level_check;

ALTER TABLE paper_presentations
    ADD CONSTRAINT paper_presentations_level_check
    CHECK (presentation_level IN ('State', 'National', 'International', 'Others'));

ALTER TABLE paper_presentations
    DROP CONSTRAINT IF EXISTS paper_presentations_status_check;

ALTER TABLE paper_presentations
    ADD CONSTRAINT paper_presentations_status_check
    CHECK (status IN ('Pending', 'Approved', 'Rejected'));

ALTER TABLE paper_presentations
    DROP CONSTRAINT IF EXISTS paper_presentations_points_nonnegative_check;

ALTER TABLE paper_presentations
    ADD CONSTRAINT paper_presentations_points_nonnegative_check
    CHECK (COALESCE(points, 0) >= 0);
