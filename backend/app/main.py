from fastapi import FastAPI

from app.config import get_settings
from app.database import create_db_and_tables
from app.routes.auth import router as auth_router
from app.routes.auth import users_router
from app.routes.health import router as health_router

get_settings()

app = FastAPI(
    title="User Authentication System",
    version="1.0.0",
    description="Backend-only authentication API for user registration, login, JWT authentication, and protected profile access.",
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(health_router)


@app.on_event("startup")
def startup_event():
    create_db_and_tables()


@app.get("/")
def root():
    return {
        "message": "SYNTECHYHUB User Authentication API",
        "docs": "/docs",
        "health": "/api/health",
    }
