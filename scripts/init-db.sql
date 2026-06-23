CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    document_type TEXT,
    source_path TEXT,
    status TEXT NOT NULL DEFAULT 'uploaded',
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    customer_external_id TEXT UNIQUE,
    name TEXT,
    segment TEXT,
    monthly_spend NUMERIC,
    tenure INTEGER,
    monthly_charges NUMERIC,
    total_charges NUMERIC,
    contract_type TEXT,
    support_tickets INTEGER DEFAULT 0,
    late_payments INTEGER DEFAULT 0,
    churn INTEGER,
    support_ticket_count INTEGER DEFAULT 0,
    unpaid_invoice_count INTEGER DEFAULT 0,
    churn_probability NUMERIC,
    risk_score NUMERIC,
    risk_level TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    rating INTEGER,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_documents_status ON documents (status);
CREATE INDEX IF NOT EXISTS ix_document_chunks_document_id ON document_chunks (document_id);
CREATE INDEX IF NOT EXISTS ix_customers_customer_external_id ON customers (customer_external_id);
