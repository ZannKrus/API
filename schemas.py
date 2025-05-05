from pydantic import BaseModel, Field, HttpUrl, validator, EmailStr
from typing import List, Optional
from datetime import datetime
import re


class GenreBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="Боевик")
    description: Optional[str] = Field(None, example="Фильмы с драками и погонями")

class GenreCreate(GenreBase):
    pass 

class Genre(GenreBase): 
    id: int

    class Config:
        from_attributes = True



class MovieBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, example="Крепкий орешек")
    release_year: Optional[int] = Field(None, ge=1888, le=datetime.now().year + 5, example=1988)
    duration_min: Optional[int] = Field(None, gt=0, example=132)
    rating: Optional[float] = Field(None, ge=0.0, le=10.0, example=8.2)
    description: Optional[str] = Field(None, example="Полицейский спасает заложников в небоскребе.")
    poster_url: Optional[str] = Field(None, max_length=500, example="/uploads/die_hard_poster.jpg")

class MovieCreate(MovieBase):
    genre_ids: List[int] = Field(..., example=[1, 5]) 

class MovieUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, example="Крепкий орешек")
    release_year: Optional[int] = Field(None, ge=1888, le=datetime.now().year + 5, example=1988)
    duration_min: Optional[int] = Field(None, gt=0, example=132)
    rating: Optional[float] = Field(None, ge=0.0, le=10.0, example=8.2)
    description: Optional[str] = Field(None, example="Полицейский спасает заложников в небоскребе.")
    genre_ids: Optional[List[int]] = Field(None, example=[1, 5])

class Movie(MovieBase):
    id: int
    created_at: datetime
    genres: List[Genre] = [] 

    class Config:
        from_attributes = True 

class UserBase(BaseModel):
    id: int
    username: str = Field(example="kino_lover")
    email: Optional[EmailStr] = Field(None, example="user@example.com")
    created_at: datetime

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=60, example="kino_lover")
    password: str = Field(..., min_length=8, max_length=60, example="SecurePwd123")
    email: Optional[EmailStr] = Field(None, example="user@example.com")

    @validator('password')
    def validate_password_complexity(cls, value):
        errors = []
        if not re.search(r"\d", value):
            errors.append("должен содержать хотя бы одну цифру")
        if not re.search(r"[a-z]", value):
            errors.append("должен содержать хотя бы одну строчную букву")
        if not re.search(r"[A-Z]", value):
            errors.append("должен содержать хотя бы одну заглавную букву")

        if errors:
            raise ValueError(f"Пароль не соответствует требованиям: {'; '.join(errors)}")

        return value