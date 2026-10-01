import os
os.environ["DATABASE_URL"] = "sqlite:///./test_transactions.db"
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.database import Base
from app.db.session import get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()
app.dependency_overrides[get_db] = override_db

@pytest.fixture
def client():
    return TestClient(app)
