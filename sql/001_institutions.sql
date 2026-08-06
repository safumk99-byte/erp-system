-- =========================================
-- Table: institutions
-- Module: Authentication
-- Version: 1.0
-- =========================================

CREATE TABLE institutions (
    id SERIAL PRIMARY KEY,

    name VARCHAR(150) NOT NULL,
    code VARCHAR(30) UNIQUE NOT NULL,

    email VARCHAR(150) UNIQUE,
    phone VARCHAR(20),

    status VARCHAR(20) DEFAULT 'active',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE institutions
ADD COLUMN address TEXT,
ADD COLUMN city VARCHAR(100),
ADD COLUMN state VARCHAR(100),
ADD COLUMN country VARCHAR(100) DEFAULT 'India',
ADD COLUMN logo TEXT,
ADD COLUMN subscription_plan VARCHAR(20) DEFAULT 'free',
ADD COLUMN subscription_start DATE,
ADD COLUMN subscription_end DATE;

INSERT INTO institutions (
    name,
    code,
    email,
    phone,
    status,
    subscription_plan
)
VALUES (
    'ERP System',
    'SYSTEM',
    'system@erp.local',
    '0000000000',
    'active',
    'premium'
);