import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "auth_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-1234567890")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

    import app.config
    import app.database
    import app.models
    import app.dependencies
    import app.routes.auth
    import app.routes.health
    import app.main

    importlib.reload(app.config)
    importlib.reload(app.database)
    importlib.reload(app.models)
    importlib.reload(app.dependencies)
    importlib.reload(app.routes.auth)
    importlib.reload(app.routes.health)
    importlib.reload(app.main)

    app.database.Base.metadata.create_all(bind=app.database.engine)

    with TestClient(app.main.app) as test_client:
        yield test_client
