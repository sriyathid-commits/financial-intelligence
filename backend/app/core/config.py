import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./financial_intelligence.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
API_PREFIX = "/api/v1"

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
