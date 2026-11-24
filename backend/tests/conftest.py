"""Pytest configuration and fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Register SQLite cross-dialect compilers for PostgreSQL and pgvector types
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "TEXT"

@compiles(UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "CHAR(36)"

try:
    from pgvector.sqlalchemy import Vector
    @compiles(Vector, "sqlite")
    def compile_vector_sqlite(type_, compiler, **kw):
        return "TEXT"
except ImportError:
    pass

from app.core.database import Base, get_db
import app.models  # Ensure all models are registered in metadata
from main import app

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create test database and session."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create test client."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_business_data():
    """Sample business data for testing."""
    return {
        "business_name": "Test Business",
        "category": "Software Development",
        "description": "A test business",
        "address": "123 Test Street",
        "city": "Lucknow",
        "state": "Uttar Pradesh",
        "country": "India",
        "website": "https://testbusiness.com",
        "source_provider": "test",
        "provider_external_id": "test123",
    }
