from sqlalchemy.orm import Session
from sqlalchemy.future import select

from db import models
from api import schemas
from core.security import get_password_hash


async def get_user_by_email(db: Session, email: str):
    query = select(models.User).filter(models.User.email == email)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
