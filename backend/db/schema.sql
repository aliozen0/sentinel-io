-- Kullanıcılar (Supabase Auth ile entegre)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID REFERENCES auth.users NOT NULL PRIMARY KEY,
  username TEXT,
  credits DECIMAL DEFAULT 0.0
);

-- İşlem Geçmişi
CREATE TABLE IF NOT EXISTS jobs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  status TEXT CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')),
  mode TEXT CHECK (mode IN ('SIMULATION', 'LIVE')),
  gpu_target TEXT, -- Örn: "RTX 4090"
  final_cost DECIMAL,
  logs_summary TEXT
);

-- Market Önbelleği (Sık sorgulanan veriler)
CREATE TABLE IF NOT EXISTS market_snapshots (
  id SERIAL PRIMARY KEY,
  captured_at TIMESTAMP DEFAULT NOW(),
  raw_data JSONB -- Tüm node listesi buraya dump edilecek
);

-- Sohbet Geçmişi
CREATE TABLE IF NOT EXISTS chat_messages (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES auth.users, -- Opsiyonel: Anonim ise null
  role TEXT CHECK (role IN ('user', 'assistant')),
  content TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- SSH Anahtarları (Adım 3 için)
CREATE TABLE IF NOT EXISTS ssh_keys (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users,
  key_name TEXT, -- Kullanıcının verdiği isim (örn: "AWS GPU Node")
  private_key_enc TEXT, -- Şifrelenmiş Private Key (Gelecekte entegre edilecek)
  public_key TEXT, -- Public Key (Sunucuya eklenecek olan)
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
