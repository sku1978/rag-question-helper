--CREATE DATABASE question_vector_db;

CREATE EXTENSION IF NOT EXISTS vector;

--DROP TABLE IF EXISTS questions;

CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    question_id TEXT,
    question_text TEXT,
    context_keywords TEXT[],
    page INTEGER,
    document_name TEXT,
    subject TEXT,
    year INTEGER,
    source_file TEXT,  
    embedding VECTOR(1536),         -- OpenAI ada-002
    load_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);