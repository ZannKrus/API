from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext

import models as m
from database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBasic()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def basic_auth(
    credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)
) -> m.User:
    user_db = db.query(m.User).filter(m.User.username == credentials.username).first()

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Basic"},
    )

    if not user_db:
        raise credentials_exception
    if not verify_password(credentials.password, user_db.hashed_password):
        raise credentials_exception

    return user_db