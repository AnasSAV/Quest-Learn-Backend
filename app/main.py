from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.session import engine
from app.db.init_db import init_db
from app.api.v1.auth import router as auth_router
from app.api.v1.teachers import router as teachers_router
from app.api.v1.students import router as students_router
from app.api.v1.classes import router as classes_router
from app.api.v1.assignments import router as assignments_router
from app.api.v1.questions import router as questions_router
from app.api.v1.attempts import router as attempts_router
from app.api.v1.results import router as results_router
from app.api.v1.uploads import router as uploads_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="Math Buddy Backend",
    description="Production-ready backend for student math homework site",
    version="1.0.0",
    docs_url="/docs" if settings.APP_ENV != "prod" else None,
    redoc_url="/redoc" if settings.APP_ENV != "prod" else None,
    lifespan=lifespan,
)

# Security middleware
if settings.APP_ENV == "prod":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.yourdomain.com", "yourdomain.com"]
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(teachers_router, prefix="/api/v1/teachers", tags=["Teachers"])
app.include_router(students_router, prefix="/api/v1/students", tags=["Students"])
app.include_router(classes_router, prefix="/api/v1/classes", tags=["Classes"])
app.include_router(assignments_router, prefix="/api/v1/assignments", tags=["Assignments"])
app.include_router(questions_router, prefix="/api/v1/questions", tags=["Questions"])
app.include_router(attempts_router, prefix="/api/v1/attempts", tags=["Attempts"])
app.include_router(results_router, prefix="/api/v1/results", tags=["Results"])
app.include_router(uploads_router, prefix="/api/v1/uploads", tags=["Uploads"])


@app.get("/")
async def root():
    return {"message": "Math Buddy Backend API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.APP_ENV == "dev"
    )
