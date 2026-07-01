-- DDL Schema for LearnLoom AI Coding Problem Generation Engine
-- Run this in your Supabase SQL Editor to initialize the database tables.

CREATE TABLE IF NOT EXISTS public.problems (
    id VARCHAR(50) PRIMARY KEY, -- e.g., LL-000001
    title TEXT NOT NULL,
    statement TEXT NOT NULL,
    difficulty VARCHAR(20) NOT NULL CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
    xp INTEGER NOT NULL DEFAULT 50,
    tags TEXT[] NOT NULL DEFAULT '{}',
    topic TEXT NOT NULL,
    concept TEXT NOT NULL,
    learning_objective TEXT NOT NULL,
    input_format TEXT NOT NULL,
    output_format TEXT NOT NULL,
    constraints TEXT[] NOT NULL DEFAULT '{}',
    starter_code JSONB NOT NULL DEFAULT '{}'::jsonb, -- python, java, c, cpp, javascript templates
    test_cases JSONB NOT NULL DEFAULT '{}'::jsonb,  -- public and hidden test cases
    hints TEXT[] NOT NULL DEFAULT '{}',             -- 3 progressive hints
    editorial JSONB NOT NULL DEFAULT '{}'::jsonb,   -- optimal, brute force, complexities, pitfalls
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Indexing for fast search filtering in LearnLoom UI
CREATE INDEX IF NOT EXISTS idx_problems_difficulty ON public.problems(difficulty);
CREATE INDEX IF NOT EXISTS idx_problems_topic ON public.problems(topic);

-- Enable Row Level Security (RLS) if desired, or grant anonymous select
ALTER TABLE public.problems ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow anonymous read access" ON public.problems
    FOR SELECT USING (true);

CREATE POLICY "Allow service role write access" ON public.problems
    FOR ALL USING (auth.role() = 'service_role');
