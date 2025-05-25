CREATE DATABASE IF NOT EXISTS question_vector_db;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    question_id TEXT,
    question_text TEXT,
    context_keywords TEXT[],
    page INTEGER,
    document_name TEXT,
    subject TEXT,
    year INTEGER,
    embedding VECTOR(1536)  -- for OpenAI 'text-embedding-ada-002'
);
