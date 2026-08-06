-- =========================================
-- Table: roles
-- Module: Authentication
-- Version: 1.0
-- =========================================

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,

    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO roles (name, description)
VALUES
('super_admin', 'System Super Administrator'),
('institution_admin', 'Institution Administrator'),
('principal', 'Principal'),
('staff', 'Teaching and Non-Teaching Staff'),
('parent', 'Parent'),
('student', 'Student');