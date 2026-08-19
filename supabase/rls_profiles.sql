-- The React frontend talks to Supabase Auth directly using the anon/publishable
-- key, so it needs RLS policies the old Streamlit app never did (Streamlit used
-- the secret key server-side, which bypasses RLS entirely).
--
-- Run this once in the Supabase SQL editor (Project > SQL Editor).

alter table profiles enable row level security;

-- Login needs to look up a profile's email by username BEFORE the user is
-- authenticated, and the signed-in Home page needs to read its own profile.
-- Exposes username/display_name/email publicly (same data the old backend
-- returned for this exact lookup) — fine for a small friends app, but revisit
-- if the user base grows or emails should stay private.
drop policy if exists "profiles are publicly readable" on profiles;
create policy "profiles are publicly readable"
  on profiles for select
  using (true);

-- Sign-up inserts a profile row right after auth.signUp() creates the user.
drop policy if exists "users can insert their own profile" on profiles;
create policy "users can insert their own profile"
  on profiles for insert
  with check (auth.uid() = user_id);
