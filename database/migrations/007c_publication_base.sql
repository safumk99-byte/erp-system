-- ALIF ERP - Publication Tracking base schema
CREATE TABLE IF NOT EXISTS publications (
    id BIGSERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    publication_type VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(20),
    pages INTEGER NOT NULL,
    publication_date DATE,
    isbn VARCHAR(100),
    verification_value VARCHAR(255),
    description TEXT,
    points NUMERIC(10,2) NOT NULL DEFAULT 0,
    bonus_points NUMERIC(10,2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    reviewed_by INTEGER,
    reviewed_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT publication_base_type_check CHECK (publication_type IN ('Article','Book')),
    CONSTRAINT publication_base_category_check CHECK (category IS NULL OR category IN ('Fiction','Non-Fiction')),
    CONSTRAINT publication_base_status_check CHECK (status IN ('Pending','Approved','Rejected')),
    CONSTRAINT publication_base_pages_check CHECK (pages > 0),
    CONSTRAINT publication_base_points_check CHECK (points >= 0 AND bonus_points >= 0)
);

CREATE INDEX IF NOT EXISTS idx_publication_base_institution_student ON publications(institution_id, student_id);
