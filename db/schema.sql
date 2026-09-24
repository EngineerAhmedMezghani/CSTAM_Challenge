CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS scrape_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    input_url TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'done', 'failed')),
    current_stage TEXT NOT NULL DEFAULT 'DISCOVERY',
    max_depth INTEGER NOT NULL DEFAULT 3,
    max_pages INTEGER NOT NULL DEFAULT 50,
    pages_visited INTEGER NOT NULL DEFAULT 0,
    pages_discovered INTEGER NOT NULL DEFAULT 0,
    tender_pages_found INTEGER NOT NULL DEFAULT 0,
    tenders_extracted INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tenders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES scrape_jobs(id) ON DELETE CASCADE,
    source_url TEXT NOT NULL,
    title TEXT,
    description TEXT,
    owner TEXT,
    contact TEXT,
    published_date DATE,
    deadline DATE,
    documents JSONB NOT NULL DEFAULT '[]'::jsonb,
    raw_html_snippet TEXT,
    extraction_method TEXT NOT NULL DEFAULT 'generic',
    page_type TEXT NOT NULL DEFAULT 'TENDER_DETAIL',
    confidence_score DOUBLE PRECISION,
    confidence_signals JSONB NOT NULL DEFAULT '{}'::jsonb,
    discovery_url TEXT,
    discovery_depth INTEGER,
    discovery_path JSONB NOT NULL DEFAULT '[]'::jsonb,
    content_hash TEXT,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_scrape_jobs_status ON scrape_jobs(status);
CREATE INDEX IF NOT EXISTS ix_tenders_job_id ON tenders(job_id);
CREATE INDEX IF NOT EXISTS ix_tenders_source_url ON tenders(source_url);
CREATE INDEX IF NOT EXISTS ix_tenders_content_hash ON tenders(content_hash);
CREATE INDEX IF NOT EXISTS ix_tenders_scraped_at ON tenders(scraped_at DESC);
