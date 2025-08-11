# Quest-Learn-Backend

A comprehensive FastAPI backend for Math Buddy, an educational platform designed for creating, managing, and grading multiple-choice question (MCQ) homework assignments with advanced classroom management and analytics.

## Overview

Math Buddy is a modern web-based educational platform that bridges the gap between teachers and students through an intuitive assignment management system. The platform enables teachers to create engaging MCQ assignments, manage virtual classrooms, and track student progress with detailed analytics, while providing students with a seamless learning experience.

## Key Features

### Authentication & Security
- **JWT-based Authentication**: Secure token-based authentication system
- **Role-based Access Control**: Granular permissions for Teachers and Students
- **OAuth2 Integration**: Compatible with FastAPI's automatic documentation
- **Password Security**: BCrypt hashing for secure password storage

### Classroom Management
- **Virtual Classrooms**: Create unlimited classrooms with unique join codes
- **Easy Enrollment**: Students join classrooms using simple 6-character codes
- **Member Management**: Track enrollment dates and classroom statistics
- **Teacher Dashboard**: Comprehensive overview of all managed classrooms

### Advanced Assignment System
- **Flexible Assignment Creation**: Rich assignments with metadata and scheduling
- **Smart Scheduling**: Set opening times and due dates with timezone support
- **Question Shuffling**: Randomize question order to prevent cheating
- **Multimedia Support**: Upload and display images for questions via Supabase
- **Time Management**: Individual time limits per question
- **Flexible Scoring**: Customizable point values for each question

### Student Experience
- **Intuitive Interface**: Clean, user-friendly assignment taking experience
- **Real-time Progress**: Live time tracking and progress indicators
- **Instant Feedback**: Immediate scoring and results after submission
- **Assignment History**: Complete history of attempts and scores
- **Multi-classroom Support**: Participate in multiple classrooms simultaneously

### Teacher Tools
- **Assignment Builder**: Intuitive interface for creating complex assignments
- **Question Bank**: Reusable question creation with image support
- **Bulk Operations**: Create multiple questions simultaneously
- **Live Monitoring**: Real-time tracking of student progress
- **Advanced Analytics**: Detailed performance metrics and trends

### Comprehensive Reporting & Analytics
- **Student Performance Reports**: Individual and classroom-wide analytics
- **Assignment Statistics**: Completion rates, average scores, and trends
- **Question Analysis**: Identify difficult questions and common mistakes
- **Progress Tracking**: Long-term student performance monitoring
- **Export Capabilities**: Generate reports for external analysis

### Multimedia & Storage
- **Image Upload**: Supabase-powered image storage for questions
- **Optimized Delivery**: Fast, reliable image serving with CDN support
- **Format Support**: PNG image format with automatic optimization
- **Security**: Signed URLs for secure file access

## Technology Stack

### Core Framework
- **FastAPI 0.111.0**: Modern, fast web framework with automatic API documentation
- **Python 3.11+**: Latest Python features and performance improvements
- **Uvicorn**: High-performance ASGI server with hot reload support

### Database & ORM
- **PostgreSQL**: Robust, scalable relational database
- **SQLAlchemy 2.0.29**: Modern Python SQL toolkit with async support
- **Psycopg**: High-performance PostgreSQL adapter

### Authentication & Security
- **PyJWT 2.8.0**: JSON Web Token implementation
- **PassLib with BCrypt**: Secure password hashing
- **CORS Middleware**: Cross-origin resource sharing configuration

### File Storage & Services
- **Supabase Storage**: Cloud storage with CDN and image optimization
- **Pydantic 2.7.1**: Data validation and settings management
- **Python-dotenv**: Environment variable management

### Testing & Development
- **Pytest 7.4.4**: Comprehensive testing framework
- **Pytest-asyncio**: Async testing support
- **HTTPX**: Modern HTTP client for testing APIs
- **Coverage**: Test coverage reporting

### Deployment & DevOps
- **Docker**: Containerization for consistent deployments
- **Railway**: Cloud platform deployment (Procfile included)
- **Gunicorn/Uvicorn**: Production WSGI/ASGI servers

## PI Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Register new user (teacher/student) |
| `POST` | `/auth/login` | User login with credentials |
| `POST` | `/auth/token` | OAuth2 compatible token endpoint |

### Teacher Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/teachers/classrooms` | Create new classroom |
| `GET` | `/teachers/classrooms/all` | List all teacher's classrooms |
| `GET` | `/teachers/classrooms/{id}/members` | Get classroom membership |
| `GET` | `/teachers/students/comprehensive-report` | Detailed student analytics |

### Student Operations
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/students/join` | Join classroom with code |
| `GET` | `/students/my-classrooms` | Get enrolled classrooms |
| `GET` | `/students/{id}/classrooms` | Get student's classroom list |

### Assignment Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/assignments` | Create new assignment |
| `GET` | `/assignments/all` | Get all assignments with stats |
| `GET` | `/assignments/classroom/{id}` | Get classroom assignments |
| `GET` | `/assignments/{id}` | Get assignment details |
| `GET` | `/assignments/{id}/questions` | Get assignment questions |
| `GET` | `/assignments/{id}/results` | Get assignment results |
| `GET` | `/assignments/student/{id}` | Get student assignment history |

### Question Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/questions` | Create single question |
| `POST` | `/questions/bulk-create` | Create multiple questions |
| `POST` | `/questions/upload-image` | Upload question image |
| `GET` | `/questions/{id}` | Get question details |
| `PUT` | `/questions/{id}` | Update question |
| `DELETE` | `/questions/{id}` | Delete question |

### Assignment Attempts
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/attempts` | Start assignment attempt |
| `POST` | `/attempts/{id}/submit` | Submit completed assignment |
| `POST` | `/attempts/{id}/responses` | Submit individual responses |
| `GET` | `/attempts/assignment/{aid}/student/{sid}` | Get attempt details |

### User Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/users/me` | Get current user profile |
| `GET` | `/users/teachers` | List all teachers |
| `GET` | `/users/students` | List all students |

## 🗄 Database Schema

### Entity Relationship Overview
```
User (Teachers/Students)
├── Classroom (Teachers create)
│   ├── ClassroomMember (Students join)
│   └── Assignment
│       ├── Question (MCQ with options)
│       └── Attempt (Student submissions)
│           └── Response (Individual answers)
└── UploadToken (Temporary file access)
```

### Core Models

#### User Model
- **Authentication**: Email, username, secure password hash
- **Roles**: TEACHER or STUDENT with appropriate permissions
- **Profile**: Full name and creation timestamp
- **Relationships**: Created classrooms, assignments, attempts

#### Classroom Model
- **Management**: Name, unique join code, teacher ownership
- **Membership**: Student enrollment tracking with join dates
- **Security**: Teacher-controlled access and member management

#### Assignment Model
- **Content**: Title, description, question collection
- **Scheduling**: Optional opening time and due date
- **Configuration**: Question shuffling, point distribution
- **Tracking**: Creation metadata and ownership

#### Question Model
- **Content**: Text prompt, optional image, four options (A-D)
- **Configuration**: Correct answer, time limit, point value
- **Organization**: Order index for consistent presentation

#### Attempt Model
- **Tracking**: Start time, submission time, status tracking
- **Scoring**: Total score calculation and validation
- **States**: IN_PROGRESS, SUBMITTED, LATE

#### Response Model
- **Answers**: Student's chosen option for each question
- **Validation**: Automatic correctness checking
- **Analytics**: Time taken per question for insights

## Setup & Installation

### Prerequisites
- **Python 3.11+**: Latest Python with modern features
- **PostgreSQL 12+**: Reliable database server
- **Supabase Account**: For file storage and CDN
- **Git**: Version control system

### Environment Configuration

Create a comprehensive `.env` file:

```env
# Application Environment
APP_ENV=development

# Database Configuration
DATABASE_URL=postgresql://username:password@hostname:port/database_name

# JWT Authentication Settings
JWT_SECRET=your-super-secret-jwt-key-minimum-32-characters
JWT_EXPIRES_MIN=30
JWT_REFRESH_EXPIRES_MIN=43200

# Supabase Storage Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_BUCKET=math-png

# CORS and Security
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,https://yourdomain.com
MAX_UPLOAD_MB=2
RATE_LIMIT=60/minute
```

### Local Development Setup

1. **Clone and Setup**:
   ```bash
   git clone https://github.com/AnasSAV/Quest-Learn-Backend
   cd Quest-Learn-Backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Initialization**:
   ```bash
   python -c "from app.db.init_db import init_db; init_db()"
   ```

4. **Start Development Server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access API Documentation**:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

### Docker Deployment

**Build and Run**:
```bash
# Build image
docker build -t math-buddy-backend .

# Run container
docker run -p 8000:8000 --env-file .env math-buddy-backend

# Docker Compose (recommended)
docker-compose up -d
```

### Production Deployment

#### Railway Platform
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway link
railway up
```

#### Manual Server Deployment
```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Testing

### Comprehensive Test Suite

The project includes extensive testing across multiple categories:

```bash
# Run all tests with coverage
python -m pytest --cov=app --cov-report=html

# Run specific test categories
python -m pytest -m "unit"      # Fast unit tests
python -m pytest -m "database"  # Database integration tests
python -m pytest -m "auth"      # Authentication tests
python -m pytest -m "slow"      # Comprehensive integration tests

# Run tests with detailed output
python -m pytest -v --tb=long

# Use the custom test runner
python run_tests.py --type unit --install
```

### Test Organization

#### Test Structure
- **`tests/test_auth.py`**: Authentication and authorization
- **`tests/test_database.py`**: Database connectivity and operations
- **`tests/test_questions.py`**: Question management and validation
- **`tests/test_imports.py`**: Module import verification
- **`tests/test_db_init.py`**: Database schema initialization
- **`tests/conftest.py`**: Shared fixtures and configuration

#### Test Categories
- **Unit Tests**: Fast, isolated component testing
- **Integration Tests**: Full API endpoint testing
- **Database Tests**: PostgreSQL connection and query testing
- **Authentication Tests**: JWT and OAuth2 flow testing

### Continuous Integration

```bash
# CI-friendly test execution
python -m pytest \
  --tb=short \
  --disable-warnings \
  --cov=app \
  --cov-report=xml \
  --junit-xml=test-results.xml
```

## Project Architecture

```
app/
├── main.py                    # FastAPI application factory
├── api/v1/                    # API version 1 routes
│   ├── __init__.py
│   ├── auth.py               # Authentication endpoints
│   ├── teachers.py           # Teacher management
│   ├── students.py           # Student operations
│   ├── assignments.py        # Assignment CRUD
│   ├── questions.py          # Question management
│   ├── attempts.py           # Assignment attempts
│   └── users.py              # User management
├── core/                     # Core application logic
│   ├── config.py            # Settings and configuration
│   └── security.py          # Security utilities (JWT, hashing)
├── db/                      # Database configuration
│   ├── base.py              # SQLAlchemy declarative base
│   ├── session.py           # Database session management
│   └── init_db.py           # Database schema initialization
├── models/                  # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── user.py              # User model (teachers/students)
│   ├── classroom.py         # Classroom and membership models
│   ├── assignment.py        # Assignment model
│   ├── question.py          # Question model with MCQ options
│   ├── attempt.py           # Attempt and response models
│   └── upload_token.py      # File upload token model
├── schemas/                 # Pydantic request/response models
│   ├── __init__.py
│   ├── auth.py              # Authentication schemas
│   ├── user.py              # User schemas
│   ├── classroom.py         # Classroom schemas
│   ├── assignment.py        # Assignment schemas
│   ├── question.py          # Question schemas
│   └── attempt.py           # Attempt and response schemas
└── services/                # Business logic services
    └── storage.py           # Supabase storage service

tests/                       # Comprehensive test suite
├── __init__.py
├── conftest.py             # Pytest configuration and fixtures
├── README.md               # Test documentation
├── test_auth.py            # Authentication testing
├── test_database.py        # Database integration testing
├── test_questions.py       # Question management testing
├── test_imports.py         # Import verification testing
└── test_db_init.py         # Database initialization testing

Config Files:
├── requirements.txt         # Python dependencies
├── pytest.ini             # Pytest configuration
├── dockerfile             # Docker container configuration
├── Procfile               # Railway/Heroku deployment
└── .env.example           # Environment variables template
```

## Configuration

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_ENV` | No | `dev` | Application environment |
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `JWT_SECRET` | Yes | - | Secret key for JWT tokens |
| `JWT_EXPIRES_MIN` | No | `30` | Token expiration time |
| `JWT_REFRESH_EXPIRES_MIN` | No | `43200` | Refresh token expiration |
| `SUPABASE_URL` | Yes | - | Supabase project URL |
| `SUPABASE_ANON_KEY` | Yes | - | Supabase anonymous key |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | - | Supabase service role key |
| `SUPABASE_BUCKET` | No | `math-png` | Storage bucket name |
| `ALLOWED_ORIGINS` | No | `localhost:*` | CORS allowed origins |
| `MAX_UPLOAD_MB` | No | `2` | Maximum file upload size |
| `RATE_LIMIT` | No | `60/minute` | API rate limiting |

### Database Configuration

**PostgreSQL Setup**:
```sql
-- Create database
CREATE DATABASE math_buddy;

-- Create user (optional)
CREATE USER math_buddy_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE math_buddy TO math_buddy_user;
```

### Supabase Storage Setup

1. **Create Supabase Project**: Visit [supabase.com](https://supabase.com)
2. **Create Storage Bucket**: Name it `math-png` (or update `SUPABASE_BUCKET`)
3. **Configure Policies**: Set appropriate RLS policies for file access
4. **Get Credentials**: Copy URL, anon key, and service role key

## 🚦 API Usage Examples

### Authentication Flow

```bash
# Register a new teacher
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teacher@example.com",
    "user_name": "teacher1",
    "password": "securepassword",
    "full_name": "John Teacher",
    "role": "TEACHER"
  }'

# Login and get token
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "teacher1",
    "password": "securepassword"
  }'
```

### Classroom Management

```bash
# Create classroom (teacher only)
curl -X POST "http://localhost:8000/teachers/classrooms" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mathematics 101"
  }'

# Student joins classroom
curl -X POST "http://localhost:8000/students/join" \
  -H "Authorization: Bearer STUDENT_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "ABC123"
  }'
```

### Assignment Creation

```bash
# Create assignment
curl -X POST "http://localhost:8000/assignments" \
  -H "Authorization: Bearer TEACHER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "classroom_id": "classroom-uuid",
    "title": "Chapter 1 Quiz",
    "description": "Basic algebra concepts",
    "opens_at": "2024-01-15T09:00:00Z",
    "due_at": "2024-01-22T23:59:59Z",
    "shuffle_questions": true
  }'
```

### Development Workflow

1. **Fork Repository**: Create your own fork
2. **Create Branch**: `git checkout -b feature/amazing-feature`
3. **Make Changes**: Implement your feature
4. **Add Tests**: Ensure proper test coverage
5. **Run Tests**: `python -m pytest`
6. **Check Style**: Follow PEP 8 guidelines
7. **Commit Changes**: Use descriptive commit messages
8. **Push Branch**: `git push origin feature/amazing-feature`
9. **Create PR**: Submit a detailed pull request

### Code Standards

- **Python Style**: Follow PEP 8 guidelines
- **Type Hints**: Use type annotations throughout
- **Documentation**: Add docstrings for all functions
- **Testing**: Maintain >90% test coverage
- **Security**: Follow security best practices

### Testing Requirements

```bash
# Before submitting PR
python -m pytest --cov=app --cov-fail-under=90
python -m black app/ tests/
python -m isort app/ tests/
python -m flake8 app/ tests/
```

**Quest Learn Backend** - Empowering education through modern technology 

