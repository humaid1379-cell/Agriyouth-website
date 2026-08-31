-- Least-privilege role bootstrap for the isolated synthetic prototype.
--
-- nabd_owner : owns the schema and runs migrations.
-- nabd_app   : the application runtime role. It can INSERT and SELECT audit_events but
--              never UPDATE or DELETE them, which is one half of the append-only control
--              (the other half is the reject trigger installed by the migration).
--
-- Passwords here are synthetic local-demo values. They are not secrets, they are not used
-- outside the isolated prototype, and they must never be reused anywhere else.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nabd_owner') THEN
    -- CREATEDB lets the owner role restore a backup into a separate local database,
    -- which is deployment-validation check 10.
    CREATE ROLE nabd_owner LOGIN CREATEDB PASSWORD 'nabd_owner_demo';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nabd_app') THEN
    CREATE ROLE nabd_app LOGIN PASSWORD 'nabd_app_demo';
  END IF;
END
$$;

-- The application role must not be able to create objects of its own.
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
