-- ALIF ERP student leave enhancements
-- Run after the base student_leave_requests and attendance tables exist.

CREATE TABLE IF NOT EXISTS student_leave_requests (
    id BIGSERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    leave_date DATE NOT NULL,
    reason TEXT NOT NULL CHECK (btrim(reason) <> ''),
    status VARCHAR(20) NOT NULL DEFAULT 'Pending'
        CHECK (status IN ('Pending', 'Approved', 'Rejected')),
    review_remarks TEXT,
    reviewed_by INTEGER,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE student_leave_requests
    ADD COLUMN IF NOT EXISTS review_remarks TEXT;

ALTER TABLE student_leave_requests
    ADD COLUMN IF NOT EXISTS reviewed_by INTEGER;

ALTER TABLE student_leave_requests
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;

ALTER TABLE student_leave_requests
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

CREATE INDEX IF NOT EXISTS ix_student_leave_institution_date
    ON student_leave_requests (institution_id, leave_date);

CREATE INDEX IF NOT EXISTS ix_student_leave_student_date
    ON student_leave_requests (student_id, leave_date);

CREATE INDEX IF NOT EXISTS ix_student_leave_status
    ON student_leave_requests (institution_id, status);

CREATE UNIQUE INDEX IF NOT EXISTS uq_student_leave_active_date
    ON student_leave_requests (institution_id, student_id, leave_date)
    WHERE status IN ('Pending', 'Approved');

ALTER TABLE attendance
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS uq_attendance_student_date_period
    ON attendance (institution_id, student_id, attendance_date, period_number);
