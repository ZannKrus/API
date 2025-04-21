Отлично! Давайте создадим API для фильмотеки на FastAPI, основываясь на вашем примере.

**1. Обновляем `.env`**

Зададим имя файла базы данных для нашего проекта.

```.env
DB_NAME=movielib.db
```

**2. Обновляем `config.py`**

Этот файл остается без изменений, так как он просто читает `.env`.

```python
# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DB_NAME: str = "movielib.db" # Можно оставить значение по умолчанию или изменить

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

**3. Обновляем `database.py`**

Этот файл также остается практически без изменений, он универсален.

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings
import os

# Создаем папку для БД, если ее нет
db_dir = os.path.dirname(f"./{settings.DB_NAME}")
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir) # Создаем директорию, если она не существует

DATABASE_URL = f"sqlite:///./{settings.DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} # нужно для sqlite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**4. Создаем/Обновляем `models.py`**

Здесь мы определим SQLAlchemy модели для `Movie` и `Genre`, а также таблицу связей (association table) для отношения "многие-ко-многим" между ними.

```python
# models.py
from sqlalchemy import (Column, Integer, String, Float, Text, DateTime,
                        ForeignKey, Table, create_engine)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # Для установки значения по умолчанию NOW()
from database import Base
import datetime

# Таблица связей для Movie и Genre (многие-ко-многим)
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

    # Связь с фильмами (для Genre -> Movies)
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
    poster_url = Column(String(500), nullable=True) # Путь к файлу или URL
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связь с жанрами (для Movie -> Genres)
    genres = relationship(
        "Genre",
        secondary=movie_genres_association,
        back_populates="movies"
    )

# Убедимся, что таблицы созданы (можно запустить один раз или оставить здесь)
# from database import engine
# Base.metadata.create_all(bind=engine) # Это лучше делать в seed.py или отдельном скрипте
```

**5. Создаем схемы Pydantic (`schemas.py`)**

Вместо директории `pyd` создадим один файл `schemas.py` для Pydantic моделей (это более распространенный подход).

```python
# schemas.py
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Optional
from datetime import datetime

# --- Genre Schemas ---

class GenreBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="Боевик")
    description: Optional[str] = Field(None, example="Фильмы с драками и погонями")

class GenreCreate(GenreBase):
    pass # Наследует все поля от GenreBase

class Genre(GenreBase): # Для ответа API (включает ID)
    id: int

    class Config:
        from_attributes = True # Для совместимости с SQLAlchemy (Pydantic v2)
        # orm_mode = True # Для Pydantic v1


# --- Movie Schemas ---

# Базовая схема для Movie (общие поля)
class MovieBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, example="Крепкий орешек")
    release_year: Optional[int] = Field(None, ge=1888, le=datetime.now().year + 5, example=1988)
    duration_min: Optional[int] = Field(None, gt=0, example=132)
    rating: Optional[float] = Field(None, ge=0.0, le=10.0, example=8.2)
    description: Optional[str] = Field(None, example="Полицейский спасает заложников в небоскребе.")
    poster_url: Optional[str] = Field(None, max_length=500, example="/uploads/die_hard_poster.jpg") # Будет обновляться отдельно

# Схема для создания Movie (принимает список ID жанров)
class MovieCreate(MovieBase):
    genre_ids: List[int] = Field(..., example=[1, 5]) # Ожидаем список ID существующих жанров

# Схема для обновления Movie (все поля опциональны)
class MovieUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, example="Крепкий орешек")
    release_year: Optional[int] = Field(None, ge=1888, le=datetime.now().year + 5, example=1988)
    duration_min: Optional[int] = Field(None, gt=0, example=132)
    rating: Optional[float] = Field(None, ge=0.0, le=10.0, example=8.2)
    description: Optional[str] = Field(None, example="Полицейский спасает заложников в небоскребе.")
    # poster_url обновляется через отдельный эндпоинт
    genre_ids: Optional[List[int]] = Field(None, example=[1, 5]) # Позволяет обновить жанры

# Схема для ответа API (включает ID, дату создания и связанные жанры)
class Movie(MovieBase):
    id: int
    created_at: datetime
    genres: List[Genre] = [] # Вложенная схема Genre для отображения жанров

    class Config:
        from_attributes = True # Для совместимости с SQLAlchemy (Pydantic v2)
        # orm_mode = True # Для Pydantic v1

```

**6. Обновляем `main.py`**

Добавим все необходимые эндпоинты.

```python
# main.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, status
from fastapi.staticfiles import StaticFiles # Для раздачи загруженных файлов
from sqlalchemy.orm import Session, joinedload # joinedload для Eager Loading
from database import get_db, engine # Импортируем engine для создания таблиц при старте (опционально)
import models as m
import schemas as s
from typing import List
import os
import shutil # Для операций с файлами
import uuid # Для генерации уникальных имен файлов
from pathlib import Path # Для работы с путями

# --- Настройки ---
UPLOAD_DIR = "uploads" # Папка для загрузки постеров
MAX_FILE_SIZE = 5 * 1024 * 1024 # 5 MB
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# Создаем папку для загрузок, если ее нет
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

# Создаем таблицы при старте приложения (если их нет)
# Это можно делать и отдельно скриптом seed.py
# m.Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Фильмотеки", description="API для управления базой данных фильмов и жанров")

# --- Монтирование статической директории ---
# Позволяет обращаться к файлам в /uploads по URL /uploads/filename.jpg
app.mount(f"/{UPLOAD_DIR}", StaticFiles(directory=UPLOAD_DIR), name=UPLOAD_DIR)


# --- Вспомогательная функция для валидации файла ---
def validate_poster(file: UploadFile):
    if not file:
        return None # Файл не предоставлен, это нормально для некоторых операций

    # Проверка расширения
    extension = file.filename.split(".")[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый тип файла. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Проверка размера (асинхронно читаем, чтобы не блокировать)
    # Обратите внимание: file.size доступен только *после* чтения файла.
    # FastAPI читает мелкие файлы в память, крупные - во временный файл.
    # Проверка размера здесь может быть неточной до полного чтения.
    # Более надежная проверка - после чтения файла.
    # if file.size > MAX_FILE_SIZE: # Эта проверка может быть ненадежной здесь
    #     raise HTTPException(
    #         status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    #         detail=f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE // 1024 // 1024}MB"
    #     )

    return file

async def save_poster(file: UploadFile) -> str:
    """Сохраняет файл постера и возвращает относительный путь."""
    # Генерируем уникальное имя файла
    extension = file.filename.split(".")[-1].lower()
    unique_filename = f"{uuid.uuid4()}.{extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        # Асинхронно записываем файл
        file_size = 0
        with open(file_path, "wb") as buffer:
            while content := await file.read(1024 * 1024): # Читаем по 1MB
                file_size += len(content)
                if file_size > MAX_FILE_SIZE:
                     os.remove(file_path) # Удаляем частично записанный файл
                     raise HTTPException(
                         status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                         detail=f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE // 1024 // 1024}MB"
                     )
                buffer.write(content)

    except Exception as e:
        # Если произошла ошибка при записи, удаляем файл (если он был создан)
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось сохранить файл: {e}"
        )
    finally:
        await file.close()

    # Возвращаем относительный путь для сохранения в БД и использования в URL
    return f"/{UPLOAD_DIR}/{unique_filename}"


# --- Эндпоинты для Жанров (Genres) ---

@app.post('/genres', response_model=s.Genre, status_code=status.HTTP_201_CREATED, tags=["Жанры"])
def create_genre(genre_in: s.GenreCreate, db: Session = Depends(get_db)):
    """Добавление нового жанра."""
    # Проверка на уникальность имени
    existing_genre = db.query(m.Genre).filter(m.Genre.name == genre_in.name).first()
    if existing_genre:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Жанр с названием '{genre_in.name}' уже существует."
        )

    db_genre = m.Genre(**genre_in.model_dump()) # Используем model_dump() для Pydantic v2
    db.add(db_genre)
    db.commit()
    db.refresh(db_genre)
    return db_genre

@app.get('/genres', response_model=List[s.Genre], tags=["Жанры"])
def get_all_genres(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получение списка всех жанров с пагинацией."""
    genres = db.query(m.Genre).offset(skip).limit(limit).all()
    return genres

# --- Эндпоинты для Фильмов (Movies) ---

@app.post('/movies', response_model=s.Movie, status_code=status.HTTP_201_CREATED, tags=["Фильмы"])
def create_movie(movie_in: s.MovieCreate, db: Session = Depends(get_db)):
    """Добавление нового фильма."""
    # Проверяем существование всех указанных жанров
    genres = db.query(m.Genre).filter(m.Genre.id.in_(movie_in.genre_ids)).all()
    if len(genres) != len(movie_in.genre_ids):
        # Находим отсутствующие ID
        found_ids = {g.id for g in genres}
        missing_ids = [gid for gid in movie_in.genre_ids if gid not in found_ids]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Жанры с ID {missing_ids} не найдены."
        )

    # Создаем объект фильма без жанров сначала
    movie_data = movie_in.model_dump(exclude={'genre_ids'}) # Исключаем genre_ids
    db_movie = m.Movie(**movie_data)

    # Добавляем найденные объекты жанров к фильму
    db_movie.genres = genres

    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    # Загружаем связанные жанры для ответа (joinedload в запросе refresh не работает напрямую)
    # Поэтому делаем отдельный запрос или используем данные из `genres`
    db_movie_with_genres = db.query(m.Movie).options(joinedload(m.Movie.genres)).filter(m.Movie.id == db_movie.id).first()
    return db_movie_with_genres


@app.get('/movies', response_model=List[s.Movie], tags=["Фильмы"])
def get_all_movies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получение списка всех фильмов с пагинацией и связанными жанрами."""
    movies = db.query(m.Movie).options(joinedload(m.Movie.genres)).offset(skip).limit(limit).all()
    # joinedload(m.Movie.genres) - эффективно загружает жанры одним доп. запросом
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
    db_movie = db.query(m.Movie).options(joinedload(m.Movie.genres)).filter(m.Movie.id == movie_id).first() # Загружаем жанры сразу
    if not db_movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Фильм не найден")

    # Обновляем поля фильма из запроса (только те, что переданы)
    update_data = movie_in.model_dump(exclude_unset=True, exclude={'genre_ids'}) # exclude_unset=True - только переданные поля
                                                                               # exclude={'genre_ids'} - обрабатываем отдельно
    for key, value in update_data.items():
        setattr(db_movie, key, value)

    # Обновляем жанры, если они переданы в запросе
    if movie_in.genre_ids is not None: # Проверяем, что список genre_ids был передан (может быть пустым [])
        # Проверяем существование новых жанров
        genres = db.query(m.Genre).filter(m.Genre.id.in_(movie_in.genre_ids)).all()
        if len(genres) != len(movie_in.genre_ids):
            found_ids = {g.id for g in genres}
            missing_ids = [gid for gid in movie_in.genre_ids if gid not in found_ids]
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Жанры с ID {missing_ids} не найдены при обновлении."
            )
        # Заменяем текущие жанры на новые
        db_movie.genres = genres

    db.commit()
    db.refresh(db_movie)
    # После refresh может потребоваться снова загрузить жанры, если они не были в joinedload
    # В данном случае joinedload был выше, поэтому db_movie уже содержит обновленные жанры
    return db_movie


@app.put('/movies/{movie_id}/image', response_model=s.Movie, tags=["Фильмы"])
async def upload_movie_poster(movie_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Обновление (загрузка) постера для фильма."""
    db_movie = db.query(m.Movie).filter(m.Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Фильм не найден")

    # Валидация файла (тип, размер обрабатывается в save_poster)
    validated_file = validate_poster(file)
    if not validated_file:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Файл постера не предоставлен")


    # Удаляем старый постер, если он был
    if db_movie.poster_url:
        old_poster_path = db_movie.poster_url.lstrip('/') # Убираем ведущий /
        if os.path.exists(old_poster_path):
            try:
                os.remove(old_poster_path)
            except OSError as e:
                print(f"Ошибка при удалении старого постера {old_poster_path}: {e}") # Логируем ошибку, но продолжаем

    # Сохраняем новый постер
    try:
        poster_path = await save_poster(validated_file)
    except HTTPException as e: # Перехватываем ошибки из save_poster (размер, запись)
        raise e # Пробрасываем дальше

    # Обновляем путь к постеру в БД
    db_movie.poster_url = poster_path
    db.commit()
    db.refresh(db_movie)
    # Перезагружаем с жанрами для корректного ответа
    db_movie_with_genres = db.query(m.Movie).options(joinedload(m.Movie.genres)).filter(m.Movie.id == movie_id).first()
    return db_movie_with_genres


@app.delete("/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Фильмы"])
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    """Удаление фильма по ID."""
    db_movie = db.query(m.Movie).filter(m.Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Фильм не найден")

     # Удаляем файл постера перед удалением записи из БД
    if db_movie.poster_url:
        poster_path = db_movie.poster_url.lstrip('/')
        if os.path.exists(poster_path):
            try:
                os.remove(poster_path)
            except OSError as e:
                print(f"Ошибка при удалении постера {poster_path} для удаляемого фильма {movie_id}: {e}")

    db.delete(db_movie)
    db.commit()
    # Для DELETE запросов обычно не возвращают тело ответа,
    # а только статус 204 No Content
    return None # FastAPI автоматически вернет 204 статус


# --- Код для запуска (если не используется uvicorn/fastapi dev) ---
# import uvicorn
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)

```

**7. Создаем `seed.py`**

Скрипт для первоначального заполнения базы данных.

```python
# seed.py
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models as m
import os

# Удаляем старую БД и папку uploads (если нужно начать с чистого листа)
DB_FILE = "movielib.db"
UPLOAD_DIR = "uploads"
if os.path.exists(DB_FILE):
    print(f"Удаление старой базы данных: {DB_FILE}")
    os.remove(DB_FILE)

if os.path.exists(UPLOAD_DIR):
    print(f"Удаление старой папки загрузок: {UPLOAD_DIR}")
    import shutil
    shutil.rmtree(UPLOAD_DIR) # Удаляем папку и все ее содержимое

# Создаем папку uploads снова
os.makedirs(UPLOAD_DIR, exist_ok=True)
print(f"Папка {UPLOAD_DIR} создана/проверена.")


# Создаем все таблицы
print("Создание таблиц...")
m.Base.metadata.create_all(bind=engine)
print("Таблицы созданы.")

print("Начало заполнения базы данных...")
# Используем сессию для добавления данных
with SessionLocal() as session:
    # --- Добавляем Жанры ---
    genre1 = m.Genre(name="Боевик", description="Фильмы с акцентом на экшн-сцены.")
    genre2 = m.Genre(name="Комедия", description="Фильмы, призванные смешить зрителя.")
    genre3 = m.Genre(name="Фантастика", description="Фильмы о вымышленных мирах, технологиях и событиях.")
    genre4 = m.Genre(name="Драма", description="Фильмы с глубоким сюжетом и персонажами.")
    genre5 = m.Genre(name="Триллер", description="Фильмы, держащие зрителя в напряжении.")

    session.add_all([genre1, genre2, genre3, genre4, genre5])
    session.flush() # Получаем ID для жанров перед их использованием в фильмах
    print("Жанры добавлены.")

    # --- Добавляем Фильмы ---
    movie1 = m.Movie(
        title="Крепкий орешек",
        release_year=1988,
        duration_min=132,
        rating=8.2,
        description="Нью-йоркский полицейский Джон Макклейн прибывает в Лос-Анджелес, чтобы помириться с женой.",
        # poster_url="/uploads/placeholder.jpg", # Можно добавить заглушку или оставить пустым
        genres=[genre1, genre5] # Связываем с жанрами Боевик и Триллер
    )

    movie2 = m.Movie(
        title="Матрица",
        release_year=1999,
        duration_min=136,
        rating=8.7,
        description="Хакер Нео узнает шокирующую правду о реальности.",
        genres=[genre1, genre3] # Связываем с жанрами Боевик и Фантастика
    )

    movie3 = m.Movie(
        title="Большой Лебовски",
        release_year=1998,
        duration_min=117,
        rating=7.8,
        description="Безработный пацифист по прозвищу «Чувак» случайно попадает в центр аферы.",
        genres=[genre2, genre5] # Связываем с жанрами Комедия и Триллер
    )

    movie4 = m.Movie(
        title="Зеленая миля",
        release_year=1999,
        duration_min=189,
        rating=9.1,
        description="История о надзирателе блока смертников и необычном заключенном.",
        genres=[genre4, genre3] # Связываем с жанрами Драма и Фантастика (элементы)
    )


    session.add_all([movie1, movie2, movie3, movie4])
    print("Фильмы добавлены.")

    # Фиксируем изменения
    session.commit()
    print("Изменения сохранены в базе данных.")

print("Заполнение базы данных завершено.")
```

**8. Обновляем `requirements.txt`**

```txt
fastapi[standard]
sqlalchemy
pydantic-settings
aiofiles
python-multipart
```

*   `aiofiles`: нужен для асинхронной работы с файлами (загрузка постеров).
*   `python-multipart`: необходим FastAPI для обработки `UploadFile` и форм данных.

**9. Обновляем `README.md`**

```markdown
# API Фильмотеки на FastAPI

Простое API для управления коллекцией фильмов и жанров.

## Настройка и Запуск

1.  **Клонировать репозиторий (если есть)**
    ```bash
    git clone <url-репозитория>
    cd <папка-проекта>
    ```

2.  **Создание виртуального окружения**
    ```bash
    # Windows
    py -m venv .venv
    # macOS/Linux
    python3 -m venv .venv
    ```

3.  **Активация виртуального окружения**
    ```bash
    # Windows (cmd/powershell)
    .venv\Scripts\activate
    # Windows (Git Bash)
    source .venv/Scripts/activate
    # macOS/Linux
    source .venv/bin/activate
    ```

4.  **Установка зависимостей**
    ```bash
    pip install -r requirements.txt
    ```

5.  **(Опционально) Первоначальное заполнение базы данных**
    Запустите скрипт `seed.py` для создания таблиц и добавления тестовых данных. Это также удалит старую БД и папку `uploads`, если они существуют.
    ```bash
    python seed.py
    ```
    *Примечание: Приложение FastAPI (`main.py`) также пытается создать таблицы при старте, если их нет, но `seed.py` дополнительно наполняет их данными.*

6.  **Запуск сервера разработки FastAPI**
    ```bash
    fastapi dev main.py
    ```
    Или с помощью Uvicorn:
    ```bash
    uvicorn main:app --reload
    ```
    * `--reload` автоматически перезапускает сервер при изменении кода.

7.  **Доступ к API**
    *   Сервер будет доступен по адресу: `http://127.0.0.1:8000`
    *   Интерактивная документация API (Swagger UI): `http://127.0.0.1:8000/docs`
    *   Альтернативная документация (ReDoc): `http://127.0.0.1:8000/redoc`

## Структура Проекта

*   `.env`: Файл с переменными окружения (имя файла БД).
*   `config.py`: Загрузка конфигурации с помощью Pydantic Settings.
*   `database.py`: Настройка подключения к базе данных SQLAlchemy.
*   `main.py`: Основной файл приложения FastAPI с определением эндпоинтов.
*   `models.py`: Модели данных SQLAlchemy (Movie, Genre).
*   `schemas.py`: Схемы Pydantic для валидации данных запросов и ответов.
*   `seed.py`: Скрипт для первоначального заполнения базы данных.
*   `requirements.txt`: Список зависимостей Python.
*   `uploads/`: Папка для хранения загруженных постеров фильмов (создается автоматически).
*   `README.md`: Этот файл.

## Эндпоинты API

См. документацию Swagger по адресу `http://127.0.0.1:8000/docs` после запуска сервера.

### Жанры (`/genres`)
*   `POST /genres`: Создать новый жанр.
*   `GET /genres`: Получить список всех жанров.

### Фильмы (`/movies`)
*   `POST /movies`: Создать новый фильм (указать `genre_ids`).
*   `GET /movies`: Получить список всех фильмов.
*   `GET /movies/{movie_id}`: Получить информацию о фильме по ID.
*   `PUT /movies/{movie_id}`: Обновить информацию о фильме (можно обновить `genre_ids`).
*   `PUT /movies/{movie_id}/image`: Загрузить/обновить постер для фильма (отправлять как `multipart/form-data`).
*   `DELETE /movies/{movie_id}`: Удалить фильм по ID.
```

**Порядок действий:**

1.  Сохраните все файлы с предложенным кодом в соответствующие имена файлов в вашем проекте.
2.  Создайте и активируйте виртуальное окружение (если еще не сделали).
3.  Установите зависимости: `pip install -r requirements.txt`.
4.  Запустите скрипт для заполнения БД: `python seed.py`.
5.  Запустите сервер: `fastapi dev main.py`.
6.  Откройте `http://127.0.0.1:8000/docs` в браузере и протестируйте API.

Теперь у вас есть полнофункциональное API для фильмотеки с CRUD-операциями для фильмов и жанров, связью "многие-ко-многим", валидацией данных и загрузкой файлов постеров.