-- ALIF ERP - Mentoring enhancements
-- Confidential student mentoring records.
-- Institution admins can view institution records; staff can view only
-- the confidential notes they personally created for their assigned students.

BEGIN;

CREATE TABLE IF NOT EXISTS mentoring_notes (
    id BIGSERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    staff_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    note_date DATE NOT NULL,
    category VARCHAR(40) NOT NULL,
    note TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT mentoring_category_check
        CHECK (category IN ('Behavioural', 'Academic', 'Personal Development')),
    CONSTRAINT mentoring_note_not_blank
        CHECK (length(btrim(note)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_mentoring_institution_student_date
    ON mentoring_notes (institution_id, student_id, note_date DESC);

CREATE INDEX IF NOT EXISTS idx_mentoring_staff_date
    ON mentoring_notes (institution_id, staff_id, note_date DESC);

CREATE INDEX IF NOT EXISTS idx_mentoring_category
    ON mentoring_notes (institution_id, category, note_date DESC);

COMMIT;
