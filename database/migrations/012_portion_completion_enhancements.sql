-- 012_portion_completion_enhancements.sql
BEGIN;

CREATE TABLE IF NOT EXISTS portion_completion (
    id BIGSERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    staff_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    completion_date DATE NOT NULL,
    completed_portion TEXT NOT NULL,
    remarks TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

WITH ranked AS (
    SELECT id, ROW_NUMBER() OVER (
        PARTITION BY institution_id, class_id, subject_id, completion_date
        ORDER BY id DESC
    ) AS rn
    FROM portion_completion
)
DELETE FROM portion_completion pc
USING ranked r
WHERE pc.id = r.id AND r.rn > 1;

CREATE UNIQUE INDEX IF NOT EXISTS uq_portion_completion_day
    ON portion_completion (institution_id, class_id, subject_id, completion_date);

CREATE INDEX IF NOT EXISTS idx_portion_completion_institution_date
    ON portion_completion (institution_id, completion_date DESC);

CREATE INDEX IF NOT EXISTS idx_portion_completion_class_subject
    ON portion_completion (institution_id, class_id, subject_id, completion_date DESC);

COMMIT;
