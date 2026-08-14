-- ALIF ERP - Staff Attendance & Leave Enhancements
-- Idempotent migration for PostgreSQL.

CREATE TABLE IF NOT EXISTS staff_attendance (
    id BIGSERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    staff_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    attendance_date DATE NOT NULL,
    period INTEGER NOT NULL CHECK (period >= 1),
    status VARCHAR(20) NOT NULL DEFAULT 'Present'
        CHECK (status IN ('Present', 'Absent', 'Leave')),
    leave_reason TEXT,
    leave_status VARCHAR(20) NOT NULL DEFAULT 'Not Required'
        CHECK (leave_status IN ('Not Required', 'Pending', 'Approved', 'Rejected')),
    remarks TEXT,
    marked_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    approved_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_staff_attendance_staff_date_period
    ON staff_attendance (staff_id, attendance_date, period);

CREATE INDEX IF NOT EXISTS idx_staff_attendance_institution_date
    ON staff_attendance (institution_id, attendance_date);

CREATE INDEX IF NOT EXISTS idx_staff_attendance_staff_date
    ON staff_attendance (staff_id, attendance_date);

CREATE INDEX IF NOT EXISTS idx_staff_attendance_leave_status
    ON staff_attendance (institution_id, leave_status)
    WHERE status = 'Leave';

ALTER TABLE staff_attendance
    ADD COLUMN IF NOT EXISTS marked_by INTEGER;
ALTER TABLE staff_attendance
    ADD COLUMN IF NOT EXISTS approved_by INTEGER;
ALTER TABLE staff_attendance
    ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ;
ALTER TABLE staff_attendance
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE staff_attendance
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE TABLE IF NOT EXISTS staff_leave_requests (
    id BIGSERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    staff_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    leave_date DATE NOT NULL,
    period INTEGER NOT NULL CHECK (period >= 1),
    reason TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending'
        CHECK (status IN ('Pending', 'Approved', 'Rejected')),
    reviewed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMPTZ,
    review_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_staff_leave_request_staff_date_period
    ON staff_leave_requests (staff_id, leave_date, period)
    WHERE status = 'Pending';

CREATE INDEX IF NOT EXISTS idx_staff_leave_requests_institution_status
    ON staff_leave_requests (institution_id, status, leave_date);

CREATE INDEX IF NOT EXISTS idx_staff_leave_requests_staff_date
    ON staff_leave_requests (staff_id, leave_date);
