# SYNTECHYHUB User Authentication API

A backend-only authentication system built with FastAPI. It provides secure registration, login, JWT authentication, protected user information, logout documentation, SQLite persistence, and automated API tests. No frontend application, custom website, or frontend server is included.

## Objective

Provide a small, independently runnable authentication API suitable for local development and backend assessment. The API validates user input, stores only bcrypt password hashes, issues short-lived signed JWT access tokens, and protects authenticated profile access.

## Features

- User registration with username, email, and password validation
- Login using either username or email
- bcrypt password hashing with no plaintext storage
- JWT access tokens with expiration handling
- Protected `/api/users/me` endpoint (with `/api/auth/me` retained for compatibility)
- SQLite database configured for local development
- API tests for auth and security flows
- Swagger UI at `/docs`

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Pydantic, PyJWT, bcrypt, Uvicorn
- Database: SQLite (ready for PostgreSQL-compatible configuration later)
- Testing: Pytest, FastAPI TestClient

## Architecture and Project Structure

```text
user-authentication-system/
├── backend/
│   ├── app/
│   │   ├── config.py          # Environment-backed settings validation
│   │   ├── database.py        # SQLAlchemy engine and session dependency
│   │   ├── dependencies.py    # Bearer JWT and current-user dependency
│   │   ├── main.py            # FastAPI application entry point
│   │   ├── models.py          # Users table
│   │   ├── schemas.py         # Pydantic request/response schemas
│   │   ├── security.py        # bcrypt and JWT helpers
│   │   └── routes/
│   │       ├── auth.py        # Registration, login, profile, logout
│   │       └── health.py      # Health probe
│   ├── tests/
│   │   ├── conftest.py        # Isolated temporary test database
│   │   └── test_auth.py       # Authentication and security tests
│   ├── .env.example
│   ├── .gitignore
│   ├── pytest.ini
│   └── requirements.txt
├── .gitignore
└── README.md
```

The backend uses dependency-injected SQLAlchemy sessions. FastAPI's built-in Swagger and ReDoc pages are documentation tools only; the application does not serve a custom HTML UI.

## Database Design

The `users` table contains:

| Column | Description |
|---|---|
| `id` | Integer primary key |
| `username` | Required, unique username |
| `email` | Required, unique normalized email |
| `password_hash` | bcrypt-compatible hash; plaintext is never stored |
| `created_at` | Account creation timestamp |
| `updated_at` | Last update timestamp |

SQLite is the default local database through `DATABASE_URL`. The SQLAlchemy setup keeps the database layer replaceable for PostgreSQL later.

## Backend Setup

Open PowerShell in the project root:

```powershell
cd user-authentication-system\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Update `.env` with a secure secret:

```env
DATABASE_URL=sqlite:///./auth.db
JWT_SECRET_KEY=replace_with_a_strong_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Generate a secure secret on Windows with:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Then start the backend:

```powershell
cd user-authentication-system\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger docs: http://127.0.0.1:8000/docs
ReDoc: http://127.0.0.1:8000/redoc

## Testing

```powershell
cd user-authentication-system\backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

## Backend API

| Method | Endpoint | Authentication | Purpose |
|---|---|---|---|
| POST | `/api/auth/register` | Public | Create a user account |
| POST | `/api/auth/login` | Public | Authenticate with username or email and receive a JWT |
| POST | `/api/auth/logout` | Public | Documents client-side token clearing for stateless JWTs |
| GET | `/api/users/me` | Bearer JWT | Return the authenticated user's profile |
| GET | `/api/auth/me` | Bearer JWT | Compatibility alias for the authenticated profile |
| GET | `/api/health` | Public | Health check |

### Example requests

Register:

```powershell
$body = @{
  username = "theepu123"
  email = "theepu@example.com"
  password = "StrongPassword123!"
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/auth/register" `
  -ContentType "application/json" `
  -Body $body
```

Login:

```powershell
$body = @{
  identifier = "theepu123"
  password = "StrongPassword123!"
} | ConvertTo-Json

$login = Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/auth/login" `
  -ContentType "application/json" `
  -Body $body
```

Authenticated profile:

```powershell
Invoke-RestMethod -Method Get `
  -Uri "http://127.0.0.1:8000/api/users/me" `
  -Headers @{ Authorization = "Bearer $($login.access_token)" }
```

## Authentication Workflow

1. Registration validates the username, email, and password using Pydantic.
2. The password is hashed with bcrypt and only the hash is stored.
3. Login looks up the normalized email or username and verifies the bcrypt hash.
4. A signed HS256 JWT is returned with `sub`, `iat`, and `exp` claims.
5. Protected routes validate the bearer token, signature, required claims, expiration, numeric subject, and corresponding database user.
6. Logout returns a message instructing the client to discard its token. Because access tokens are stateless, logout does not revoke a copied token server-side.

## Security Notes

- Passwords are hashed with bcrypt before storage.
- JWTs are signed using a secret from the environment.
- JWT verification explicitly allows only the configured HS256 algorithm.
- The signing key is loaded from `backend/.env` and is never returned by an API.
- Tokens are stateless. Clearing a client-side token does not instantly revoke a copied JWT in transit or already stored elsewhere.
- The logout endpoint documents client-side token disposal; it does not claim server-side token revocation.

## Known Limitations

- The implementation uses SQLite for local dev; a PostgreSQL deployment would require a different DSN and SQLAlchemy engine config.
- Logout is handled on the client side because JWTs are stateless and a server-side revoke list would need a proper denylist implementation.

## Troubleshooting

- If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

- If the backend cannot start, ensure `.env` contains a valid `JWT_SECRET_KEY`.
- Never commit `.env`, `auth.db`, virtual environments, or test caches. The repository ignore rules exclude them.

## Deployment Considerations

- Use a strong, separate JWT secret in production.
- Move from SQLite to PostgreSQL or another production database.
- Put the backend behind HTTPS and use secure headers.
