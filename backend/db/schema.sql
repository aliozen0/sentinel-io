-- ==========================================
-- io-Guard v1.5 - Consolidated SQLite Schema (Local Mode)
-- ==========================================

-- 1. Profiles (User Management)
CREATE TABLE IF NOT EXISTS profiles (
  id TEXT PRIMARY KEY,
  username TEXT UNIQUE,
  credits DECIMAL(10, 2) DEFAULT 0.0,
  password_hash TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Jobs (Transaction & Activity Log)
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  user_id TEXT,
  status TEXT, -- PENDING, RUNNING, COMPLETED, FAILED
  mode TEXT,   -- SIMULATION, LIVE, ANALYSIS
  gpu_target TEXT,
  final_cost DECIMAL(10, 2),
  logs_summary TEXT,
  metadata TEXT, -- JSON payload stored as TEXT in SQLite
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES profiles(id)
);

-- 3. Chat History
CREATE TABLE IF NOT EXISTS chat_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT,
  role TEXT,
  content TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES profiles(id)
);

-- 4. Documents Metadata (Content stored in ChromaDB for Local Mode)
-- Even though ChromaDB stores vectors/content, keeping metadata in SQL allows listing without loading heavy vector DB.
CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  source TEXT NOT NULL,
  content TEXT,  -- Optional cache
  metadata TEXT, -- JSON payload
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES profiles(id)
);

-- 5. Market Snapshots (Sniper Agent Data)
CREATE TABLE IF NOT EXISTS market_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  captured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  raw_data TEXT -- JSON
);

-- 6. SSH Keys (For Remote Deployments)
CREATE TABLE IF NOT EXISTS ssh_keys (
  id TEXT PRIMARY KEY,
  user_id TEXT,
  key_name TEXT,
  private_key_enc TEXT,
  public_key TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES profiles(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_user_id ON chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
