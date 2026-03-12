-- 1. Add user_id column to tables
ALTER TABLE asset_classes ADD COLUMN user_id UUID REFERENCES auth.users(id) DEFAULT auth.uid();
ALTER TABLE portfolio ADD COLUMN user_id UUID REFERENCES auth.users(id) DEFAULT auth.uid();
ALTER TABLE history ADD COLUMN user_id UUID REFERENCES auth.users(id) DEFAULT auth.uid();
ALTER TABLE settings ADD COLUMN user_id UUID REFERENCES auth.users(id) DEFAULT auth.uid();

-- 2. Update Constraints (to allow unique names/tickers per user)
ALTER TABLE asset_classes DROP CONSTRAINT IF EXISTS asset_classes_name_key;
ALTER TABLE asset_classes ADD CONSTRAINT asset_classes_user_name_key UNIQUE (user_id, name);

ALTER TABLE portfolio DROP CONSTRAINT IF EXISTS portfolio_ticker_key;
ALTER TABLE portfolio ADD CONSTRAINT portfolio_user_ticker_key UNIQUE (user_id, ticker);

ALTER TABLE history DROP CONSTRAINT IF EXISTS history_date_key;
ALTER TABLE history ADD CONSTRAINT history_user_date_key UNIQUE (user_id, date);

ALTER TABLE settings DROP CONSTRAINT IF EXISTS settings_pkey;
ALTER TABLE settings ADD PRIMARY KEY (user_id, key);

-- 3. Enable RLS (Row Level Security) - This ensures users only access their own data
ALTER TABLE asset_classes ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolio ENABLE ROW LEVEL SECURITY;
ALTER TABLE history ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- 4. Create Policies
CREATE POLICY "Users can only access their own asset_classes" ON asset_classes FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can only access their own portfolio" ON portfolio FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can only access their own history" ON history FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can only access their own settings" ON settings FOR ALL USING (auth.uid() = user_id);

-- Price cache can remain global or per user, let's keep it global for efficiency (no RLS needed if shared)
-- but if we want to add user_id there too:
-- ALTER TABLE price_cache ADD COLUMN user_id UUID REFERENCES auth.users(id) DEFAULT auth.uid();
