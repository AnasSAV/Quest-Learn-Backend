# Math Buddy Backend

A production-ready backend for a student math homework site built with FastAPI, PostgreSQL, and Supabase.

## Features

- **Role-based Authentication**: JWT-based auth with Teacher/Student roles
- **Classroom Management**: Teachers create classrooms, students join with codes
- **Timed Assignments**: MCQ assignments with per-question timers
- **Image Storage**: PNG question images stored in Supabase storage
- **Real-time Grading**: Automatic grading with immediate feedback
- **Results & Analytics**: Detailed results and CSV exports for teachers
- **Rate Limiting**: Built-in API rate limiting
- **Async Operations**: Fully async FastAPI implementation

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy 2.0/SQLModel
- **Authentication**: JWT (access/refresh tokens)
- **Storage**: Supabase Storage for images
- **Migrations**: Alembic
- **Testing**: pytest with async support
- **Validation**: Pydantic v2

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── core/            # Core configuration and security
│   ├── db/              # Database configuration and initialization
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic services
│   └── main.py          # FastAPI application
├── alembic/             # Database migrations
├── tests/               # Test suite
├── .env                 # Environment variables
├── requirements.txt     # Python dependencies
└── start.py             # Startup script
```

## Setup

1. **Clone and install dependencies**:
```bash
git clone <repository-url>
cd Math-Buddy-Backend
pip install -r requirements.txt
```

2. **Configure environment**:
   - Copy `.env` and update with your database and Supabase credentials
   - Set up PostgreSQL database
   - Create Supabase project and storage bucket

3. **Run migrations**:
```bash
alembic upgrade head
```

4. **Start development server**:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once running, visit:
- **Interactive docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Key Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/refresh` - Refresh access token

### Teachers
- `POST /api/v1/teachers/classrooms` - Create classroom
- `GET /api/v1/teachers/classrooms` - List teacher's classrooms
- `POST /api/v1/teachers/classrooms/{id}/invite` - Generate invite code

### Students
- `POST /api/v1/students/join` - Join classroom with code

### Assignments
- `POST /api/v1/assignments` - Create assignment
- `GET /api/v1/assignments/{id}/start` - Start assignment attempt
- `POST /api/v1/attempts/{id}/answer` - Submit answer
- `GET /api/v1/assignments/{id}/results` - View results

## Testing

```bash
pytest
pytest --cov=app tests/
```

## Database Schema

The application uses the following main entities:
- **User**: Teachers and students with role-based access
- **Classroom**: Virtual classrooms with invite codes
- **Assignment**: Timed homework assignments
- **Question**: MCQ questions with PNG images
- **Attempt**: Student assignment attempts
- **Response**: Individual question responses

## Development

- **Code formatting**: `black app tests`
- **Import sorting**: `isort app tests`
- **Type checking**: `mypy app`
- **Linting**: `flake8 app tests`

## License

MIT License
