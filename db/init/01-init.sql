-- Runs once on first Postgres startup (empty data volume).
-- Enable pgvector in the main application database.
CREATE EXTENSION IF NOT EXISTS vector;

-- Separate database for n8n's own state (workflows, executions, credentials).
SELECT 'CREATE DATABASE n8n'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'n8n')\gexec
