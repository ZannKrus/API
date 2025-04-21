from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, status
from fastapi.staticfiles import StaticFiles 
from sqlalchemy.orm import Session, joinedload 
from database import get_db, engine 
import models as m
import schemas as s
from typing import List
import os
import shutil 
import uuid 
from pathlib import Path 

UPLOAD_DIR = "uploads" 
MAX_FILE_SIZE = 5 * 1024 * 1024 # 5 MB
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

app = FastAPI(title="API Фильмотеки", description="API для управления базой данных фильмов и жанров")

app.mount(f"/{UPLOAD_DIR}", StaticFiles(directory=UPLOAD_DIR), name=UPLOAD_DIR)


def validate_poster(file: UploadFile):
    if not file:
        return None 

    extension = file.filename.split(".")[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый тип файла. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    return file

async def save_poster(file: UploadFile) -> str:
    """Сохраняет файл постера и возвращает относительный путь."""
    extension = file.filename.split(".")[-1].lower()
    unique_filename = f"{uuid.uuid4()}.{extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        file_size = 0
        with open(file_path, "wb") as buffer:
            while content := await file.read(1024 * 1024): 
                file_size += len(content)
                if file_size > MAX_FILE_SIZE:
                     os.remove(file_path) 
                     raise HTTPException(
                         status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                         detail=f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE // 1024 // 1024}MB"
                     )
                buffer.write(content)

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось сохранить файл: {e}"
        )
    finally:
        await file.close()

    return f"/{UPLOAD_DIR}/{unique_filename}"



@app.post('/genres', response_model=s.Genre, status_code=status.HTTP_201_CREATED, tags=["Жанры"])
def create_genre(genre_in: s.GenreCreate, db: Session = Depends(get_db)):
    """Добавление нового жанра."""
    existing_genre = db.query(m.Genre).filter(m.Genre.name == genre_in.name).first()
    if existing_genre:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Жанр с названием '{genre_in.name}' уже существует."
        )

    db_genre = m.Genre(**genre_in.model_dump()) 
    db.add(db_genre)
    db.commit()
    db.refresh(db_genre)
    return db_genre

@app.get('/genres', response_model=List[s.Genre], tags=["Жанры"])
def get_all_genres(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получение списка всех жанров с пагинацией."""
    genres = db.query(m.Genre).offset(skip).limit(limit).all()
    return genres


@app.post('/movies', response_model=s.Movie, status_code=status.HTTP_201_CREATED, tags=["Фильмы"])
def create_movie(movie_in: s.MovieCreate, db: Session = Depends(get_db)):
    """Добавление нового фильма."""
    genres = db.query(m.Genre).filter(m.Genre.id.in_(movie_in.genre_ids)).all()
    if len(genres) != len(movie_in.genre_ids):
        found_ids = {g.id for g in genres}
        missing_ids = [gid for gid in movie_in.genre_ids if gid not in found_ids]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Жанры с ID {missing_ids} не найдены."
        )

    movie_data = movie_in.model_dump(exclude={'genre_ids'}) 
    db_movie = m.Movie(**movie_data)

    db_movie.genres = genres

    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    db_movie_with_genres = db.query(m.Movie).options(joinedload(m.Movie.genres)).filter(m.Movie.id == db_movie.id).first()
    return db_movie_with_genres


@app.get('/movies', response_model=List[s.Movie], tags=["Фильмы"])
def get_all_movies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получение списка всех фильмов с пагинацией и связанными жанрами."""
    movies = db.query(m.Movie).options(joinedload(m.Movie.genres)).offset(skip).limit(limit).all()
    return movies

@app.get('/movies/{movie_id}', response_model=s.Movie, tags=["Фильмы"])
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    """Получение детальной информации о фильме по ID."""
    db_movie = db.query(m.Movie).options(joinedload(m.Movie.genres)).filter(m.Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Фильм не найден")
    return db_movie

@app.put('/movies/{movie_id}', response_model=s.Movie, tags=["Фильмы"])
def update_movie(movie_id: int, movie_in: s.MovieUpdate, db: Session = Depends(get_db)):
    """Обновление информации о фильме."""
    db_movie = db.query(m.Movie).options(joinedload(m.Movie.genres)).filter(m.Movie.id == movie_id).first() 
    if not db_movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Фильм не найден")

    update_data = movie_in.model_dump(exclude_unset=True, exclude={'genre_ids'}) 
                                                                               
    for key, value in update_data.items():
        setattr(db_movie, key, value)

    if movie_in.genre_ids is not None:
        genres = db.query(m.Genre).filter(m.Genre.id.in_(movie_in.genre_ids)).all()
        if len(genres) != len(movie_in.genre_ids):
            found_ids = {g.id for g in genres}
            missing_ids = [gid for gid in movie_in.genre_ids if gid not in found_ids]
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Жанры с ID {missing_ids} не найдены при обновлении."
            )
        db_movie.genres = genres

    db.commit()
    db.refresh(db_movie)
    return db_movie


@app.put('/movies/{movie_id}/image', response_model=s.Movie, tags=["Фильмы"])
async def upload_movie_poster(movie_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Обновление (загрузка) постера для фильма."""
    db_movie = db.query(m.Movie).filter(m.Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Фильм не найден")

    validated_file = validate_poster(file)
    if not validated_file:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Файл постера не предоставлен")


    if db_movie.poster_url:
        old_poster_path = db_movie.poster_url.lstrip('/')
        if os.path.exists(old_poster_path):
            try:
                os.remove(old_poster_path)
            except OSError as e:
                print(f"Ошибка при удалении старого постера {old_poster_path}: {e}")

    try:
        poster_path = await save_poster(validated_file)
    except HTTPException as e: 
        raise e 

    db_movie.poster_url = poster_path
    db.commit()
    db.refresh(db_movie)
    db_movie_with_genres = db.query(m.Movie).options(joinedload(m.Movie.genres)).filter(m.Movie.id == movie_id).first()
    return db_movie_with_genres


@app.delete("/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Фильмы"])
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    """Удаление фильма по ID."""
    db_movie = db.query(m.Movie).filter(m.Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Фильм не найден")

    if db_movie.poster_url:
        poster_path = db_movie.poster_url.lstrip('/')
        if os.path.exists(poster_path):
            try:
                os.remove(poster_path)
            except OSError as e:
                print(f"Ошибка при удалении постера {poster_path} для удаляемого фильма {movie_id}: {e}")

    db.delete(db_movie)
    db.commit()
    
    return None