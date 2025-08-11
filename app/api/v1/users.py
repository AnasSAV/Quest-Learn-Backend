from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from ...db.session import get_db
from .auth import get_current_user, CurrentUser
from ...models.user import User, UserRole
from ...schemas.user import UserOut

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserOut)
def get_current_user_info(user: CurrentUser = Depends(get_current_user)):
    """Get current authenticated user's information"""
    return user

@router.get("/by-username", response_model=UserOut)
def get_user_by_username(
    user_name: str = Query(..., description="Username to search for"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get user information by email address"""

    # Find user by username
    user = db.query(User).filter(User.user_name == user_name).first()
    
    if not user:
        raise HTTPException(404, "User not found with this email address")
    
    # Privacy check: Users can only look up their own information
    # Teachers can look up students in their classes (for now, allow all teacher lookups)
    # Students can only look up their own info
    if current_user.role == UserRole.STUDENT.value:
        if current_user.user_name != user_name:
            raise HTTPException(403, "Students can only look up their own information")
    elif current_user.role == UserRole.TEACHER.value:
        # Teachers can look up any user's basic info (for classroom management)
        pass
    else:
        raise HTTPException(403, "Invalid user role")
    
    return user

@router.get("/search", response_model=list[UserOut])
def search_users(
    email: Optional[str] = Query(None, description="Email to search for (partial match)"),
    role: Optional[str] = Query(None, description="User role to filter by (STUDENT or TEACHER)"),
    name: Optional[str] = Query(None, description="Name to search for (partial match)"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Search for users based on various criteria"""
    
    # Only teachers can search for other users
    if current_user.role != UserRole.TEACHER.value:
        raise HTTPException(403, "Only teachers can search for other users")
    
    # Build query
    query = db.query(User)
    
    # Apply filters
    if email:
        query = query.filter(User.email.ilike(f"%{email}%"))
    
    if role:
        if role.upper() not in ["STUDENT", "TEACHER"]:
            raise HTTPException(400, "Role must be either STUDENT or TEACHER")
        query = query.filter(User.role == role.upper())
    
    if name:
        query = query.filter(User.full_name.ilike(f"%{name}%"))
    
    # Limit results to prevent abuse
    users = query.limit(50).all()
    
    return users

@router.get("/{user_id}", response_model=UserOut)
def get_user_by_id(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get user information by user ID"""
    
    # Find user by ID
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(404, "User not found")
    
    # Privacy check: Users can only look up their own information
    # Teachers can look up students (for classroom management)
    if current_user.role == UserRole.STUDENT.value:
        if str(current_user.id) != user_id:
            raise HTTPException(403, "Students can only access their own information")
    elif current_user.role == UserRole.TEACHER.value:
        # Teachers can look up any user's basic info
        pass
    else:
        raise HTTPException(403, "Invalid user role")
    
    return user
