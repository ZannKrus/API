from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models as m
import os

DB_FILE = "movielib.db"
UPLOAD_DIR = "uploads"
if os.path.exists(DB_FILE):
    print(f"Удаление старой базы данных: {DB_FILE}")
    os.remove(DB_FILE)

if os.path.exists(UPLOAD_DIR):
    print(f"Удаление старой папки загрузок: {UPLOAD_DIR}")
    import shutil
    shutil.rmtree(UPLOAD_DIR) 

os.makedirs(UPLOAD_DIR, exist_ok=True)
print(f"Папка {UPLOAD_DIR} создана/проверена.")


print("Создание таблиц...")
m.Base.metadata.create_all(bind=engine)
print("Таблицы созданы.")

print("Начало заполнения базы данных...")
with SessionLocal() as session:
    genre1 = m.Genre(name="Боевик", description="Фильмы с акцентом на экшн-сцены.")
    genre2 = m.Genre(name="Комедия", description="Фильмы, призванные смешить зрителя.")
    genre3 = m.Genre(name="Фантастика", description="Фильмы о вымышленных мирах, технологиях и событиях.")
    genre4 = m.Genre(name="Драма", description="Фильмы с глубоким сюжетом и персонажами.")
    genre5 = m.Genre(name="Триллер", description="Фильмы, держащие зрителя в напряжении.")

    session.add_all([genre1, genre2, genre3, genre4, genre5])
    session.flush() 
    print("Жанры добавлены.")

    movie1 = m.Movie(
        title="Крепкий орешек",
        release_year=1988,
        duration_min=132,
        rating=8.2,
        description="Нью-йоркский полицейский Джон Макклейн прибывает в Лос-Анджелес, чтобы помириться с женой.",
        genres=[genre1, genre5] 
    )

    movie2 = m.Movie(
        title="Матрица",
        release_year=1999,
        duration_min=136,
        rating=8.7,
        description="Хакер Нео узнает шокирующую правду о реальности.",
        genres=[genre1, genre3] 
    )

    movie3 = m.Movie(
        title="Большой Лебовски",
        release_year=1998,
        duration_min=117,
        rating=7.8,
        description="Безработный пацифист по прозвищу «Чувак» случайно попадает в центр аферы.",
        genres=[genre2, genre5] 
    )

    movie4 = m.Movie(
        title="Зеленая миля",
        release_year=1999,
        duration_min=189,
        rating=9.1,
        description="История о надзирателе блока смертников и необычном заключенном.",
        genres=[genre4, genre3] 
    )


    session.add_all([movie1, movie2, movie3, movie4])
    print("Фильмы добавлены.")

    session.commit()
    print("Изменения сохранены в базе данных.")

print("Заполнение базы данных завершено.")