from typing import List

from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from sqlmodel import Session, select

from dundie.db import ActiveSession
from dundie.models.user import User, UserRequest, UserResponse
from dundie.auth import SuperUser
from sqlalchemy.exc import IntegrityError

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def list_users(*, session: Session = ActiveSession):
    """List all users."""
    users = session.exec(select(User)).all()
    return users


@router.get("/{username}/", response_model=UserResponse)
async def get_user_by_username(
    *, session: Session = ActiveSession, username: str
):
    """Get user by username"""
    query = select(User).where(User.username == username)
    user = session.exec(query).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=UserResponse, status_code=201, dependencies=[SuperUser])
async def create_user(*, session: Session = ActiveSession, user: UserRequest):
    """Creates new user"""
    if session.exec(select(User).where(User.username == user.username)).first():
        raise HTTPException(status_code=409, detail="Username already taken")

    db_user = User.from_orm(user)  # transform UserRequest in User
    session.add(db_user)
    try:
        session.commit()
    except IntegrityError:
        raise HTTPException(status_code=500, detail="Database Integrity Error")

    session.refresh(db_user)
    return db_user
