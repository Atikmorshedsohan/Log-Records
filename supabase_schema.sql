-- =====================================================================
-- Run this in your Supabase SQL Editor:
-- https://supabase.com/dashboard/project/yckcqbkuwkwvnwwwcfqi/sql/new
-- =====================================================================

-- 1. Ensure computer_events has RLS enabled
ALTER TABLE public.computer_events ENABLE ROW LEVEL SECURITY;

-- 2. Drop existing conflicting policy if any
DROP POLICY IF EXISTS "Allow anon insert to computer_events" ON public.computer_events;
DROP POLICY IF EXISTS "Allow anon select on computer_events" ON public.computer_events;

-- 3. Policy: Allow your backend collector to insert log events
CREATE POLICY "Allow anon insert to computer_events"
ON public.computer_events
FOR INSERT
TO anon
WITH CHECK (true);

-- 4. Policy: Allow reading computer_events (for dashboard / queries)
CREATE POLICY "Allow anon select on computer_events"
ON public.computer_events
FOR SELECT
TO anon
USING (true);
