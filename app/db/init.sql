CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(100),
    hashed_password VARCHAR(255) NOT NULL,
    disabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_full_name ON users(full_name);

INSERT INTO users (username, full_name, hashed_password, disabled)
VALUES 
    ('admin', 'Administrator', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', false),
    ('iazhbanov', 'Жбанов Илья', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', false),
    ('natasha', 'Иванова Наталья', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', false)
ON CONFLICT (username) DO NOTHING;