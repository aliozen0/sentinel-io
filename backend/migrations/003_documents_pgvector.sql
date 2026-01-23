-- ===========================================
-- io-Guard v1.5 - Supabase pgvector Setup
-- ===========================================
-- Bu migration'ı Supabase SQL Editor'da çalıştırın

-- 1. pgvector extension'ı aktifleştir (zaten aktif olabilir)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Documents tablosu oluştur (ÇOKLU KULLANICI DESTEĞİ)
CREATE TABLE IF NOT EXISTS public.documents (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,  -- Kullanıcı sahipliği
    content TEXT NOT NULL,
    embedding vector(384),  -- all-MiniLM-L6-v2 modeli 384 boyutlu embedding üretir
    source TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Embedding için index oluştur (hızlı arama için)
CREATE INDEX IF NOT EXISTS documents_embedding_idx 
    ON public.documents 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- 4. Source ve user_id bazlı index (filtreleme için)
CREATE INDEX IF NOT EXISTS documents_source_idx 
    ON public.documents (source);

CREATE INDEX IF NOT EXISTS documents_user_idx 
    ON public.documents (user_id);

-- 5. Semantik arama fonksiyonu (RPC) - KULLANICI BAZLI
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(384),
    match_count INT DEFAULT 5,
    filter_user_id UUID DEFAULT NULL  -- Opsiyonel: sadece bu kullanıcının dokümanları
)
RETURNS TABLE (
    id TEXT,
    content TEXT,
    source TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
SECURITY DEFINER  -- RLS bypass için gerekli
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id,
        d.content,
        d.source,
        d.metadata,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM public.documents d
    WHERE (filter_user_id IS NULL OR d.user_id = filter_user_id)
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 6. RLS (Row Level Security) - ÇOKLU KULLANICI İÇİN AKTİF
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

-- Kullanıcılar sadece kendi dokümanlarını görebilir
CREATE POLICY "Users can view own documents"
    ON public.documents FOR SELECT
    USING (auth.uid() = user_id);

-- Kullanıcılar sadece kendi adlarına doküman ekleyebilir
CREATE POLICY "Users can insert own documents"
    ON public.documents FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Kullanıcılar sadece kendi dokümanlarını silebilir
CREATE POLICY "Users can delete own documents"
    ON public.documents FOR DELETE
    USING (auth.uid() = user_id);

-- ===========================================
-- DOĞRULAMA SORGULARI
-- ===========================================

-- Extension kontrolü:
-- SELECT * FROM pg_extension WHERE extname = 'vector';

-- Tablo kontrolü:
-- SELECT * FROM public.documents LIMIT 5;

-- Fonksiyon kontrolü:
-- SELECT proname FROM pg_proc WHERE proname = 'match_documents';
