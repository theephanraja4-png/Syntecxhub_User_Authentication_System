from datetime import datetime, timedelta

import jwt

from app.config import get_settings


def test_successful_registration(client):
    response = client.post("/api/auth/register", json={"username": "alice", "email": "alice@example.com", "password": "StrongPassword123!"})
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Registration successful"
    assert data["user"]["username"] == "alice"
    assert "password_hash" not in data["user"]


def test_duplicate_username_rejected(client):
    client.post("/api/auth/register", json={"username": "alice", "email": "alice@example.com", "password": "StrongPassword123!"})
    response = client.post("/api/auth/register", json={"username": "alice", "email": "other@example.com", "password": "StrongPassword123!"})
    assert response.status_code == 409


def test_duplicate_email_rejected(client):
    client.post("/api/auth/register", json={"username": "alice", "email": "alice@example.com", "password": "StrongPassword123!"})
    response = client.post("/api/auth/register", json={"username": "bob", "email": "alice@example.com", "password": "StrongPassword123!"})
    assert response.status_code == 409


def test_invalid_email_rejected(client):
    response = client.post("/api/auth/register", json={"username": "alice", "email": "bad-email", "password": "StrongPassword123!"})
    assert response.status_code == 422


def test_password_hashing_works():
    from app.security import get_password_hash, verify_password

    hashed = get_password_hash("StrongPassword123!")
    assert hashed != "StrongPassword123!"
    assert verify_password("StrongPassword123!", hashed)


def test_successful_login(client):
    client.post("/api/auth/register", json={"username": "alice", "email": "alice@example.com", "password": "StrongPassword123!"})
    response = client.post("/api/auth/login", json={"identifier": "alice", "password": "StrongPassword123!"})
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "alice"


def test_invalid_password_rejected(client):
    client.post("/api/auth/register", json={"username": "alice", "email": "alice@example.com", "password": "StrongPassword123!"})
    response = client.post("/api/auth/login", json={"identifier": "alice", "password": "WrongPassword123!"})
    assert response.status_code == 401


def test_unknown_username_rejected(client):
    response = client.post("/api/auth/login", json={"identifier": "ghost", "password": "StrongPassword123!"})
    assert response.status_code == 401


def test_login_with_email(client):
    client.post("/api/auth/register", json={"username": "alice", "email": "alice@example.com", "password": "StrongPassword123!"})
    response = client.post("/api/auth/login", json={"identifier": "alice@example.com", "password": "StrongPassword123!"})
    assert response.status_code == 200
    assert response.json()["user"]["email"] == "alice@example.com"


def test_protected_endpoint_requires_valid_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401

    client.post("/api/auth/register", json={"username": "alice", "email": "alice@example.com", "password": "StrongPassword123!"})
    token = client.post("/api/auth/login", json={"identifier": "alice", "password": "StrongPassword123!"}).json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "alice"


def test_users_me_endpoint_returns_authenticated_user(client):
    client.post("/api/auth/register", json={"username": "alice", "email": "alice@example.com", "password": "StrongPassword123!"})
    token = client.post("/api/auth/login", json={"identifier": "alice", "password": "StrongPassword123!"}).json()["access_token"]
    response = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"id": 1, "username": "alice", "email": "alice@example.com"}


def test_deleted_user_token_is_rejected(client):
    client.post("/api/auth/register", json={"username": "alice", "email": "alice@example.com", "password": "StrongPassword123!"})
    token = client.post("/api/auth/login", json={"identifier": "alice", "password": "StrongPassword123!"}).json()["access_token"]

    from app.database import SessionLocal
    from app.models import User

    db = SessionLocal()
    try:
        db.query(User).filter(User.username == "alice").delete()
        db.commit()
    finally:
        db.close()

    response = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_malformed_token_rejected(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer malformed-token"})
    assert response.status_code == 401


def test_invalid_subject_token_rejected(client):
    settings = get_settings()
    token = jwt.encode({"sub": "not-an-integer", "exp": datetime.utcnow() + timedelta(minutes=30), "iat": datetime.utcnow()}, settings["JWT_SECRET_KEY"], algorithm=settings["JWT_ALGORITHM"])
    response = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_expired_token_rejected(client):
    settings = get_settings()
    expired = jwt.encode({"sub": "1", "exp": datetime.utcnow() - timedelta(minutes=1), "iat": datetime.utcnow() - timedelta(minutes=2)}, settings["JWT_SECRET_KEY"], algorithm=settings["JWT_ALGORITHM"])
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_tampered_token_rejected(client):
    settings = get_settings()
    token = jwt.encode({"sub": "1", "exp": datetime.utcnow() + timedelta(minutes=30), "iat": datetime.utcnow()}, settings["JWT_SECRET_KEY"], algorithm=settings["JWT_ALGORITHM"])
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token[:-1]}Z"})
    assert response.status_code == 401


def test_password_hash_not_exposed(client):
    response = client.post("/api/auth/register", json={"username": "alice", "email": "alice@example.com", "password": "StrongPassword123!"})
    payload = response.json()
    assert "password_hash" not in payload["user"]
    assert "password_hash" not in str(payload)


def test_logout_behavior(client):
    client.post("/api/auth/register", json={"username": "alice", "email": "alice@example.com", "password": "StrongPassword123!"})
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert "Logout successful" in response.json()["message"]


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
