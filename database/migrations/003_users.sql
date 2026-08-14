-- =========================================
-- Table: users
-- Module: Authentication
-- Version: 1.0
-- =========================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,

    institution_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,

    full_name VARCHAR(150) NOT NULL,

    username VARCHAR(100) NOT NULL,
    email VARCHAR(150),
    phone VARCHAR(20),

    password TEXT NOT NULL,

    is_active BOOLEAN DEFAULT TRUE,

    last_login TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_users_institution
        FOREIGN KEY (institution_id)
        REFERENCES institutions(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_users_role
        FOREIGN KEY (role_id)
        REFERENCES roles(id)
);

INSERT INTO users (
    institution_id,
    role_id,
    full_name,
    username,
    email,
    phone,
    password,
    is_active
)
VALUES (
    1,
    1,
    'Super Administrator',
    'superadmin',
    'admin@erp.local',
    '0000000000',
    'scrypt:32768:8:1$ACZUULg9me5rIHTM$46586d0bf3f891c0f415c85cb63508760a313f712291efb5967972f2eb2ad8fd6764caaab3a6f68aa7ce172a2e4b7e310310f0f0809e09c034535b3134604a2b',
    TRUE
);