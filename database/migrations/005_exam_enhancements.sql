-- ALIF ERP: Exam & Marks enhancements
-- Adds the proposal-required Main/Model distinction while preserving existing exams.

ALTER TABLE exams
    ADD COLUMN IF NOT EXISTS exam_mode VARCHAR(20);

UPDATE exams
SET exam_mode = 'Main'
WHERE exam_mode IS NULL OR TRIM(exam_mode) = '';

ALTER TABLE exams
    ALTER COLUMN exam_mode SET DEFAULT 'Main';

ALTER TABLE exams
    ALTER COLUMN exam_mode SET NOT NULL;

ALTER TABLE exams
    DROP CONSTRAINT IF EXISTS exams_exam_mode_check;

ALTER TABLE exams
    ADD CONSTRAINT exams_exam_mode_check
    CHECK (exam_mode IN ('Main', 'Model'));

CREATE UNIQUE INDEX IF NOT EXISTS uq_exam_subject
    ON exam_subjects (exam_id, subject_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_exam_mark
    ON exam_marks (exam_id, subject_id, student_id);
