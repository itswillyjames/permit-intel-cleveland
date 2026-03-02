-- Initial schema for Permit Arbitrage Intelligence Hub

CREATE TABLE IF NOT EXISTS permits (
    id SERIAL PRIMARY KEY,
    raw_json JSONB,
    permit_id TEXT,
    city TEXT,
    address TEXT,
    lat FLOAT,
    lon FLOAT,
    permit_type TEXT,
    description TEXT,
    valuation NUMERIC,
    status TEXT,
    filed_date DATE,
    issued_date DATE,
    applicant TEXT,
    contractor TEXT,
    owner TEXT,
    source_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scores (
    id SERIAL PRIMARY KEY,
    permit_id INTEGER REFERENCES permits(id),
    win_score FLOAT,
    value_score FLOAT,
    delay_score FLOAT,
    commercial_score FLOAT,
    competition_score FLOAT,
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS enrichments (
    id SERIAL PRIMARY KEY,
    permit_id INTEGER REFERENCES permits(id),
    type TEXT,
    data JSONB,
    url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS packages (
    id SERIAL PRIMARY KEY,
    permit_id INTEGER REFERENCES permits(id),
    vertical TEXT,
    content JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    city TEXT UNIQUE,
    urls JSONB,
    last_fetch TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
