-- ALIF ERP - Reading Skill Assessment base schema
CREATE TABLE IF NOT EXISTS reading_submissions (
    id BIGSERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    book_title VARCHAR(255) NOT NULL,
    reading_type VARCHAR(20) NOT NULL,
    pages INTEGER NOT NULL,
    review TEXT NOT NULL,
    points NUMERIC(10,2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    submitted_by INTEGER,
    reviewed_by INTEGER,
    reviewed_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT reading_type_check CHECK (reading_type IN ('Fiction','Non-Fiction')),
    CONSTRAINT reading_status_check CHECK (status IN ('Pending','Approved','Rejected')),
    CONSTRAINT reading_pages_check CHECK (pages > 0),
    CONSTRAINT reading_points_nonnegative_check CHECK (points >= 0)
);

CREATE INDEX IF NOT EXISTS idx_reading_institution_student ON reading_submissions(institution_id, student_id);

-- ALIF ERP - Reading Skill Assessment enhancements
-- Tracks who submitted a reading record for auditability.

ALTER TABLE reading_submissions
    ADD COLUMN IF NOT EXISTS submitted_by INTEGER;

CREATE INDEX IF NOT EXISTS idx_reading_submissions_student_status
    ON reading_submissions (student_id, status);

CREATE INDEX IF NOT EXISTS idx_reading_submissions_institution_status
    ON reading_submissions (institution_id, status);

CREATE INDEX IF NOT EXISTS idx_reading_submissions_submitted_by
    ON reading_submissions (submitted_by);
