-- Phase 3 Migration: Add columns for Citation Matrix and Organization
DO $$ 
BEGIN 
    -- 1. Status Tracking
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='papers' AND column_name='reading_status') THEN
        ALTER TABLE papers ADD COLUMN reading_status TEXT DEFAULT 'Unread'; -- Unread, Reading, Synthesized
    END IF;

    -- 2. Taggability
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='papers' AND column_name='tags') THEN
        ALTER TABLE papers ADD COLUMN tags TEXT[] DEFAULT '{}';
    END IF;

    -- 3. Impact Metrics (if not already present)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='papers' AND column_name='citation_count') THEN
        ALTER TABLE papers ADD COLUMN citation_count INTEGER DEFAULT 0;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='papers' AND column_name='impact_score') THEN
        ALTER TABLE papers ADD COLUMN impact_score FLOAT DEFAULT 0.0;
    END IF;
END $$;
