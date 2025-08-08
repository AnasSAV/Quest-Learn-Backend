from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import get_settings
from .api.v1 import auth as auth_routes
from .api.v1 import teachers as teacher_routes
from .api.v1 import students as student_routes
from .api.v1 import assignments as assignment_routes
from .api.v1 import questions as question_routes
from .api.v1 import attempts as attempt_routes

settings = get_settings()
app = FastAPI(title="MCQ Homework Grader API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(teacher_routes.router)
app.include_router(student_routes.router)
app.include_router(assignment_routes.router)
app.include_router(question_routes.router)
app.include_router(attempt_routes.router)

@app.get("/healthz")
def healthz():
    return {"ok": True}