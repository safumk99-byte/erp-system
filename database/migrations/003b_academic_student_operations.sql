-- ALIF ERP canonical Academic & Student Operations schema
-- Recovered from current Phase 40 services. No new business fields are invented.

-- Student attendance: one record per student/date/period.
CREATE TABLE IF NOT EXISTS attendance (
    id BIGSERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    attendance_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('Present','Late','Absent','Leave')),
    marked_by INTEGER NOT NULL REFERENCES users(id),
    period_number INTEGER NOT NULL CHECK (period_number BETWEEN 1 AND 8),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_attendance_student_date_period UNIQUE (institution_id, student_id, attendance_date, period_number)
);

CREATE INDEX IF NOT EXISTS ix_attendance_institution_date
    ON attendance(institution_id, attendance_date);
CREATE INDEX IF NOT EXISTS ix_attendance_student_date
    ON attendance(student_id, attendance_date);
CREATE INDEX IF NOT EXISTS ix_attendance_class_scope
    ON attendance(institution_id, student_id, attendance_date, period_number);

-- Exams. The current service creates one exam and associates multiple subjects
-- through exam_subjects; therefore subject_id remains nullable for compatibility.
CREATE TABLE IF NOT EXISTS exams (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    class_id INTEGER NOT NULL REFERENCES classes(id),
    subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    exam_name VARCHAR(200) NOT NULL,
    exam_type VARCHAR(30) NOT NULL,
    exam_mode VARCHAR(20) NOT NULL DEFAULT 'Main' CHECK (exam_mode IN ('Main','Model')),
    exam_date DATE NOT NULL,
    total_mark NUMERIC(10,2) NOT NULL CHECK (total_mark > 0 AND total_mark <= 1000),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_exams_institution_date
    ON exams(institution_id, exam_date);
CREATE INDEX IF NOT EXISTS ix_exams_class
    ON exams(institution_id, class_id);

-- Subjects belonging to an exam.
CREATE TABLE IF NOT EXISTS exam_subjects (
    id SERIAL PRIMARY KEY,
    exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    CONSTRAINT uq_exam_subject_canonical UNIQUE (exam_id, subject_id)
);

CREATE INDEX IF NOT EXISTS ix_exam_subjects_subject
    ON exam_subjects(subject_id);

-- Marks are stored per exam + subject + student.
CREATE TABLE IF NOT EXISTS exam_marks (
    id BIGSERIAL PRIMARY KEY,
    exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    mark NUMERIC(10,2) NOT NULL CHECK (mark >= 0),
    grade VARCHAR(20),
    entered_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_exam_mark_canonical UNIQUE (exam_id, subject_id, student_id)
);

CREATE INDEX IF NOT EXISTS ix_exam_marks_student
    ON exam_marks(student_id, exam_id);
CREATE INDEX IF NOT EXISTS ix_exam_marks_exam_subject
    ON exam_marks(exam_id, subject_id);

-- Student promotion history.
CREATE TABLE IF NOT EXISTS student_promotions (
    id BIGSERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    academic_year_id INTEGER NOT NULL REFERENCES academic_years(id),
    from_class_id INTEGER REFERENCES classes(id) ON DELETE SET NULL,
    to_class_id INTEGER NOT NULL REFERENCES classes(id),
    promotion_date DATE NOT NULL,
    remarks TEXT,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_student_promotions_institution_date
    ON student_promotions(institution_id, promotion_date DESC);
CREATE INDEX IF NOT EXISTS ix_student_promotions_student
    ON student_promotions(student_id, promotion_date DESC);
