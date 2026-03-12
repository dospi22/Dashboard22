-- Create Asset Classes table
CREATE TABLE asset_classes (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    target_percentage REAL NOT NULL
);

-- Create Portfolio table
CREATE TABLE portfolio (
    id SERIAL PRIMARY KEY,
    ticker TEXT UNIQUE NOT NULL,
    name TEXT,
    asset_class_id INTEGER REFERENCES asset_classes(id),
    quantity REAL NOT NULL,
    avg_price REAL NOT NULL,
    currency TEXT
);

-- Create History table
CREATE TABLE history (
    id SERIAL PRIMARY KEY,
    date TEXT UNIQUE NOT NULL,
    total_value REAL NOT NULL,
    invested_capital REAL NOT NULL
);

-- Create Settings table
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Create Price Cache table
CREATE TABLE price_cache (
    ticker TEXT PRIMARY KEY,
    price REAL NOT NULL,
    last_updated TEXT NOT NULL
);

-- Initial settings
INSERT INTO settings (key, value) VALUES ('tolerance', '5') ON CONFLICT (key) DO NOTHING;
