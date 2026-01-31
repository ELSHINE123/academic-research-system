-- 1. Create Projects Table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    client_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Create Papers Table
CREATE TABLE IF NOT EXISTS papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    authors TEXT[], -- Array of author names
    year INTEGER,
    abstract TEXT,
    url TEXT,
    methodology TEXT,
    summary TEXT,
    citation_count INTEGER DEFAULT 0,
    source_type TEXT DEFAULT 'external', -- 'external', 'internal', 'manual', 'snowball'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Enable RLS (Row Level Security)
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE papers ENABLE ROW LEVEL SECURITY;

-- 4. Create Indexes for fast text search
CREATE INDEX IF NOT EXISTS idx_papers_title ON papers USING GIN (to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_papers_abstract ON papers USING GIN (to_tsvector('english', abstract));
CREATE INDEX IF NOT EXISTS idx_papers_project_id ON papers(project_id);

-- Note: For simple password-gated apps, we often use a single service role or anon key.
-- In a real multi-tenant app, we would use Supabase Auth and link user_id to these tables.
