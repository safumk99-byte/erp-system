-- ALIF ERP - Writing Skill Assessment base schema
CREATE TABLE IF NOT EXISTS writing_submissions (
    id BIGSERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    writing_type VARCHAR(20) NOT NULL,
    pages INTEGER NOT NULL,
    content TEXT NOT NULL,
    points NUMERIC(10,2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    submitted_by INTEGER,
    reviewed_by INTEGER,
    reviewed_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT writing_base_type_check CHECK (writing_type IN ('Fiction','Non-Fiction')),
    CONSTRAINT writing_base_status_check CHECK (status IN ('Pending','Approved','Rejected')),
    CONSTRAINT writing_base_pages_check CHECK (pages > 0),
    CONSTRAINT writing_base_points_check CHECK (points >= 0)
);

CREATE INDEX IF NOT EXISTS idx_writing_institution_student ON writing_submissions(institution_id, student_id);

-- Writing Skill Assessment enhancements
-- Safe to run on an existing PostgreSQL installation.

ALTER TABLE writing_submissions
    ADD COLUMN IF NOT EXISTS submitted_by INTEGER;

CREATE INDEX IF NOT EXISTS ix_writing_institution_student
    ON writing_submissions (institution_id, student_id);

CREATE INDEX IF NOT EXISTS ix_writing_institution_status
    ON writing_submissions (institution_id, status);

CREATE INDEX IF NOT EXISTS ix_writing_student_status
    ON writing_submissions (student_id, status);

-- Keep application values aligned with the proposal workflow.
ALTER TABLE writing_submissions
    DROP CONSTRAINT IF EXISTS writing_submissions_type_check;

ALTER TABLE writing_submissions
    ADD CONSTRAINT writing_submissions_type_check
    CHECK (writing_type IN ('Fiction', 'Non-Fiction'));

ALTER TABLE writing_submissions
    DROP CONSTRAINT IF EXISTS writing_submissions_status_check;

ALTER TABLE writing_submissions
    ADD CONSTRAINT writing_submissions_status_check
    CHECK (status IN ('Pending', 'Approved', 'Rejected'));

ALTER TABLE writing_submissions
    DROP CONSTRAINT IF EXISTS writing_submissions_pages_check;

ALTER TABLE writing_submissions
    ADD CONSTRAINT writing_submissions_pages_check
    CHECK (pages > 0);
