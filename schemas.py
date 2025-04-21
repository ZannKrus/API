from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Optional
from datetime import datetime


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