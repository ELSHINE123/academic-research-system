-- MIGRATION SCRIPT: Fix missing owner_id columns

-- 1. Add owner_id to projects if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='projects' AND column_name='owner_id') THEN
        ALTER TABLE projects ADD COLUMN owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT auth.uid();
    END IF;
END $$;

-- 2. Add owner_id to papers if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='papers' AND column_name='owner_id') THEN
        ALTER TABLE papers ADD COLUMN owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT auth.uid();
    END IF;
END $$;

-- 3. Now it is safe to enable RLS and Policies
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE papers ENABLE ROW LEVEL SECURITY;

-- 4. Drop old policies if they exist (to avoid duplication errors)
DROP POLICY IF EXISTS "Users can only manage their own projects" ON projects;
DROP POLICY IF EXISTS "Users can only manage their own papers" ON papers;

-- 5. Create Fresh Policies
CREATE POLICY "Users can only manage their own projects" ON projects FOR ALL USING (auth.uid() = owner_id);
CREATE POLICY "Users can only manage their own papers" ON papers FOR ALL USING (auth.uid() = owner_id);

-- 6. Add Indexes
CREATE INDEX IF NOT EXISTS idx_papers_owner_id ON papers(owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id);
