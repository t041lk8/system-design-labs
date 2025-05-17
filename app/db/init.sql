CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(100),
    hashed_password VARCHAR(255) NOT NULL,
    disabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS services (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(username),
    total_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_services (
    order_id UUID REFERENCES orders(id),
    service_id UUID REFERENCES services(id),
    PRIMARY KEY (order_id, service_id)
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_full_name ON users(full_name);
CREATE INDEX IF NOT EXISTS idx_services_name ON services(name);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_order_services_order_id ON order_services(order_id);
CREATE INDEX IF NOT EXISTS idx_order_services_service_id ON order_services(service_id);

INSERT INTO users (username, full_name, hashed_password, disabled)
VALUES 
    ('admin', 'Administrator', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', false),
    ('iazhbanov', 'Жбанов Илья', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', false)
    ('natasha', 'Иванова Наталья', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', false)
ON CONFLICT (username) DO NOTHING;

INSERT INTO services (id, name, description, price)
VALUES 
    ('86b423fd-950c-4052-b4ca-4933b88da587', 'Покраска обоев', 'Покаршу обои недорого', 100.00),
    ('ee720ea8-c166-4d0e-98a0-f48d169022b2', 'Пишу лабы', 'Сделаю лабы по программной инженерии', 12000.00),
    ('45578523-f257-484d-97b3-ddb9092a0121', 'Фотографирую на заказ', 'Профессиональный фотограф из ПГТ Бобруйск', 500.00),
    ('9100e555-a198-45d6-83c2-49ae8ef52cc0', 'Профессиональный игрок в CS2', 'Выиграю любые матчи в контр страйк', 1300.00)
ON CONFLICT (id) DO NOTHING;

INSERT INTO orders (id, user_id, total_price, created_at)
VALUES 
    ('d235ab9c-0213-4600-bb6f-21bed122aa24', 'admin', 800.00, CURRENT_TIMESTAMP),
    ('a5997eee-6bf7-4190-85da-d7427acdfcad', 'iazhbanov', 550.00, CURRENT_TIMESTAMP),
    ('7fe39bc9-d372-40d5-8958-5caef2e98934', 'natasha', 1050.00, CURRENT_TIMESTAMP)
ON CONFLICT (id) DO NOTHING;

INSERT INTO order_services (order_id, service_id)
VALUES 
    ('d235ab9c-0213-4600-bb6f-21bed122aa24', '86b423fd-950c-4052-b4ca-4933b88da587'),
    ('d235ab9c-0213-4600-bb6f-21bed122aa24', '45578523-f257-484d-97b3-ddb9092a0121'),
    ('d235ab9c-0213-4600-bb6f-21bed122aa24', '9100e555-a198-45d6-83c2-49ae8ef52cc0'),
    
    ('a5997eee-6bf7-4190-85da-d7427acdfcad', '86b423fd-950c-4052-b4ca-4933b88da587'),
    ('a5997eee-6bf7-4190-85da-d7427acdfcad', '45578523-f257-484d-97b3-ddb9092a0121'),
    
    ('7fe39bc9-d372-40d5-8958-5caef2e98934', '86b423fd-950c-4052-b4ca-4933b88da587'),
    ('7fe39bc9-d372-40d5-8958-5caef2e98934', '9100e555-a198-45d6-83c2-49ae8ef52cc0'),
    ('7fe39bc9-d372-40d5-8958-5caef2e98934', 'ee720ea8-c166-4d0e-98a0-f48d169022b2')
ON CONFLICT (order_id, service_id) DO NOTHING;