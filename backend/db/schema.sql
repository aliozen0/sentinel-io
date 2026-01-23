-- Hybrid Schema (SQLite Compatible)

-- Profiles (Mimics Supabase 'profiles' linked to auth.users)
CREATE TABLE IF NOT EXISTS profiles (
  id TEXT PRIMARY KEY,
  username TEXT UNIQUE,
  credits DECIMAL(10, 2) DEFAULT 0.0,
  password_hash TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Jobs / Transaction History
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  user_id TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  status TEXT, -- PENDING, RUNNING, COMPLETED, FAILED
  mode TEXT, -- SIMULATION, LIVE, ANALYSIS
  gpu_target TEXT,
  final_cost DECIMAL(10, 2),
  logs_summary TEXT,
  metadata TEXT, -- JSON payload for job details
  FOREIGN KEY(user_id) REFERENCES profiles(id)
);

-- Market Snapshots
-- SQLite doesn't have JSONB, use TEXT for JSON payload
CREATE TABLE IF NOT EXISTS market_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  captured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  raw_data TEXT
);

-- Chat History
CREATE TABLE IF NOT EXISTS chat_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT,
  role TEXT,
  content TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES profiles(id)
);

-- SSH Keys
CREATE TABLE IF NOT EXISTS ssh_keys (
  id TEXT PRIMARY KEY,
  user_id TEXT,
  key_name TEXT,
  private_key_enc TEXT,
  public_key TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES profiles(id)
);

-- Documents (v1.5 RAG Knowledge Base)
-- NOT: SQLite'da vector tipi yok, ChromaDB vektörleri saklar
-- Bu tablo sadece metadata için (LOCAL modda ChromaDB kullanılır)
CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,          -- Doküman sahibi
  source TEXT NOT NULL,           -- Dosya adı
  content TEXT,                   -- Doküman içeriği (opsiyonel, chunk'lar için)
  metadata TEXT,                  -- JSON: chunk_index, total_chunks, file_type
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES profiles(id)
);
