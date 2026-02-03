-- Add content_body column to papers table for full-text storage
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='papers' AND column_name='content_body') THEN
        ALTER TABLE papers ADD COLUMN content_body TEXT;
    END IF;
END $$;
