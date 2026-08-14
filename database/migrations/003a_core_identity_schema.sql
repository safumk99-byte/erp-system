-- ALIF ERP canonical core identity schema
-- Recovered from the current Phase 40 application services/routes.
-- No legacy tables (such as separate staff/parents tables) are invented:
-- staff and parents are represented by users + roles.

-- Institution admission-number configuration used by student_service.
ALTER TABLE institutions
    ADD COLUMN IF NOT EXISTS admission_prefix VARCHAR(30);

-- Academic years
CREATE TABLE IF NOT EXISTS academic_years (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    year_name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_academic_year_name UNIQUE (institution_id, year_name),
    CONSTRAINT chk_academic_year_dates CHECK (end_date > start_date)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_academic_year_current
    ON academic_years(institution_id)
    WHERE is_current = TRUE;

-- Classes
CREATE TABLE IF NOT EXISTS classes (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    class_name VARCHAR(150) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_class_name_per_institution UNIQUE (institution_id, class_name)
);

-- Subjects belong to a class in the current application architecture.
CREATE TABLE IF NOT EXISTS subjects (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_name VARCHAR(150) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_subject_per_class UNIQUE (institution_id, class_id, subject_name)
);

-- Staff-to-class assignments. Staff are users whose role is staff/principal.
CREATE TABLE IF NOT EXISTS staff_classes (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    staff_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_staff_class UNIQUE (staff_id, class_id)
);

-- Staff-to-subject assignments.
CREATE TABLE IF NOT EXISTS staff_subjects (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    staff_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_staff_subject UNIQUE (staff_id, subject_id)
);

-- Students. Parent/student authentication is represented by users.role_id;
-- parent_user_id and user_id link those accounts to the student record.
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    admission_no VARCHAR(50) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    gender VARCHAR(20) NOT NULL,
    date_of_birth DATE,
    class_id INTEGER NOT NULL REFERENCES classes(id),
    parent_name VARCHAR(150) NOT NULL,
    parent_phone VARCHAR(30) NOT NULL,
    address TEXT,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE SET NULL,
    parent_user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_student_admission_per_institution UNIQUE (institution_id, admission_no),
    CONSTRAINT chk_student_gender CHECK (gender IN ('Male','Female','Other'))
);

CREATE INDEX IF NOT EXISTS idx_students_institution_class
    ON students(institution_id, class_id);
CREATE INDEX IF NOT EXISTS idx_students_parent_user
    ON students(parent_user_id);
CREATE INDEX IF NOT EXISTS idx_staff_classes_scope
    ON staff_classes(institution_id, staff_id, class_id);
CREATE INDEX IF NOT EXISTS idx_staff_subjects_scope
    ON staff_subjects(institution_id, staff_id, subject_id);
CREATE INDEX IF NOT EXISTS idx_subjects_class
    ON subjects(institution_id, class_id);
