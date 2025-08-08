from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...models.user import User, UserRole
from ...core.security import hash_password, verify_password, create_token, decode_token
from ...schemas.auth import RegisterRequest, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# OAuth2 scheme for FastAPI docs login
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",  # This is the endpoint that will be called for login
    description="Login with your email and password to get access token"
)

# Alternative HTTPBearer for manual token input (if needed)
manual_security = HTTPBearer(
    scheme_name="BearerAuth",
    description="Enter your JWT token manually (get it from /auth/login or /auth/register)",
    auto_error=False
)

# Type alias for the current user
CurrentUser = User

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> CurrentUser:
    """
    Dependency to get the current authenticated user from JWT token.
    Works with OAuth2 login form in FastAPI docs.
    """
    try:
        # Decode the JWT token
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get the user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

@router.post("/token", response_model=TokenResponse)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login for FastAPI docs.
    Use your email as username and your password.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_token(str(user.id), user.role.value)
    return TokenResponse(access_token=token, token_type="bearer")

@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if payload.role not in ("TEACHER", "STUDENT"):
        raise HTTPException(400, "role must be TEACHER or STUDENT")
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="email already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password), role=UserRole(payload.role), full_name=payload.full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(str(user.id), user.role.value)
    return TokenResponse(access_token=token, token_type="bearer")

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    token = create_token(str(user.id), user.role.value)
    return TokenResponse(access_token=token, token_type="bearer")