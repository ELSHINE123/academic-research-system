-- 1. Profiles Table (linked to Supabase Auth)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    agency_name TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Projects Table (with user isolation)
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT auth.uid(),
    name TEXT NOT NULL,
    client_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Papers Table (with user isolation)
CREATE TABLE IF NOT EXISTS papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT auth.uid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    authors TEXT[],
    year INTEGER,
    abstract TEXT,
    url TEXT,
    methodology TEXT,
    summary TEXT,
    citation_count INTEGER DEFAULT 0,
    source_type TEXT DEFAULT 'external',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Enable RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE papers ENABLE ROW LEVEL SECURITY;

-- 5. RLS Policies (Owner-only access)
CREATE POLICY "Users can only see their own profile" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can only manage their own projects" ON projects FOR ALL USING (auth.uid() = owner_id);
CREATE POLICY "Users can only manage their own papers" ON papers FOR ALL USING (auth.uid() = owner_id);

-- 6. Indexes
CREATE INDEX IF NOT EXISTS idx_papers_owner_id ON papers(owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_papers_title ON papers USING GIN (to_tsvector('english', title));
