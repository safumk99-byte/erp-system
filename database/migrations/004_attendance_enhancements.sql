-- ALIF ERP attendance enhancements
-- Run after the base attendance table exists.

ALTER TABLE attendance
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS uq_attendance_student_date_period
    ON attendance (institution_id, student_id, attendance_date, period_number);

CREATE TABLE IF NOT EXISTS speaker_forum_attendance (
    id BIGSERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    attendance_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('Present','Absent','Leave')),
    duration_minutes INTEGER NOT NULL DEFAULT 0 CHECK (duration_minutes >= 0),
    marked_by INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_speaker_forum_attendance UNIQUE (institution_id, student_id, attendance_date)
);

CREATE INDEX IF NOT EXISTS ix_speaker_forum_institution_date
    ON speaker_forum_attendance (institution_id, attendance_date);
CREATE INDEX IF NOT EXISTS ix_speaker_forum_student
    ON speaker_forum_attendance (student_id, attendance_date);
