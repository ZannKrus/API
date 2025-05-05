from sqlalchemy import (Column, Integer, String, Float, Text, DateTime,
                        ForeignKey, Table, create_engine)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func 
from database import Base
import datetime

movie_genres_association = Table(
    'movie_genres', Base.metadata,
    Column('movie_id', Integer, ForeignKey('movies.id'), primary_key=True),
    Column('genre_id', Integer, ForeignKey('genres.id'), primary_key=True)
)

class Genre(Base):
    __tablename__ = "genres"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    movies = relationship(
        "Movie",
        secondary=movie_genres_association,
        back_populates="genres"
    )

class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    release_year = Column(Integer, nullable=True)
    duration_min = Column(Integer, nullable=True)
    rating = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    poster_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    genres = relationship(
        "Genre",
        secondary=movie_genres_association,
        back_populates="movies"
    )

class User(Base):
    __tablename__ = "users"
    id = Column(Integer(), primary_key=True, autoincrement=True, nullable=False)
    username = Column(String(60), nullable=False, unique=True, index=True) 
    hashed_password = Column(String(255), nullable=False) 
    email = Column(String(255), nullable=True, unique=True, index=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())