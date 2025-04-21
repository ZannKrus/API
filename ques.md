config.py:
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DB_NAME:str = "default"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

database.py:
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

engine = create_engine(
    f"sqlite:///./{settings.DB_NAME}.sqlite",
    connect_args={"check_same_thread": False}# нужно для sqlite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base=declarative_base()

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

main.py:
from fastapi import FastAPI, HTTPException, Depends
from database import get_db
from sqlalchemy.orm import Session
import models as m
from typing import List
import pyd

app=FastAPI()

@app.get('/products', response_model=List[pyd.BaseProduct])
def get_all_products(db:Session=Depends(get_db)):
    products=db.query(m.Product).all()
    return products

@app.get('/product/{product_id}', response_model=pyd.BaseProduct)
def get_product(product_id:int,db:Session=Depends(get_db)):
    product=db.query(m.Product).filter(
        m.Product.id==product_id
    ).first()

    if not product:
        raise HTTPException(404, 'Товар не найден')
    return product

@app.post('/product', response_model=pyd.BaseProduct)
def create_product(product:pyd.CreateProduct, db:Session=Depends(get_db)):
    product_db=db.query(m.Product).filter(m.Product.name == product.name).first()
    if product_db:
        raise HTTPException(400, "Такой товар уже есть")
    product_db=m.Product()
    product_db.name=product.name

    db.add(product_db)
    db.commit()
    return(product_db)

@app.delete("/product/{product_id}")
def delete_product(product_id:int,db:Session=Depends(get_db)):
    product=db.query(m.Product).filter(m.Product.id==product_id).first()

    if not product:
        raise HTTPException(404, 'Товар не найден')
    db.delete(product)
    db.commit()
    return {"msg": "Товар удален"}





@app.get('/types', response_model=List[pyd.BaseType])
def get_all_types(db:Session=Depends(get_db)):
    types=db.query(m.Type).all()
    return types

@app.get('/types/{types_id}', response_model=pyd.BaseType)
def get_type(type_id:int,db:Session=Depends(get_db)):
    type=db.query(m.Type).filter(
        m.Type.id==type_id
    ).first()

    if not type:
        raise HTTPException(404, 'Тип не найден')
    return type

@app.post('/type', response_model=pyd.BaseType)
def create_Type(type:pyd.CreateType, db:Session=Depends(get_db)):
    # type_db=db.query(m.Type).filter(m.Type.name == type.name).first()
    # if type_db:
    #     raise HTTPException(400, "Такой товар уже есть")
    type_db=m.Type()
    type_db.name=type.name
    type_db.undertype=type.undertype

    db.add(type_db)
    db.commit()
    return(type_db)

models.py:
from database import Base
from sqlalchemy import Column, Integer, String

class Product(Base):
    __tablename__="products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True)

class Type(Base):
    __tablename__="type"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    undertype = Column(String(255))

pyd\__init__.py:
from .base_models import *
from .create_models import *

pyd\base_models.py:
from pydantic import BaseModel, Field

class BaseProduct(BaseModel):
    id:int=Field(example=1)
    name:str=Field(example="Молоко")

class BaseType(BaseModel):
    id:int=Field(example=1)
    name:str=Field(example="Электроника")
    undertype:str=Field(example="Телефон")

pyd\base_models.py:
from pydantic import BaseModel, Field

class BaseProduct(BaseModel):
    id:int=Field(example=1)
    name:str=Field(example="Молоко")

class BaseType(BaseModel):
    id:int=Field(example=1)
    name:str=Field(example="Электроника")
    undertype:str=Field(example="Телефон")

pyd\create_models.py:
from pydantic import BaseModel, Field

class CreateProduct(BaseModel):
    name:str=Field(min_length=3, max_length=255, example="Молоко")

class CreateType(BaseModel):
    name:str=Field(min_length=3, max_length=255, example="Электроника")
    undertype:str=Field(min_length=3, max_length=255, example="Телефон")

.env:
DB_NAME=product.db

seed.py:
from sqlalchemy.orm import Session
from database import engine
import models as m

m.Base.metadata.drop_all(bind=engine)
m.Base.metadata.create_all(bind=engine)

with Session(bind=engine) as session:
    p1=m.Product(name='Молоко')
    session.add(p1)

    p1=m.Type(name="Электроника", undertype="Телефон")
    session.add(p1)

    session.commit()

requirements.txt:
fastapi[standard]
sqlalchemy
pydantic-settings

README.md:
Создание venv
`py -m venv .venv`

Активация venv
`.venv\\Scripts\\activate`

Установка зависимостей
`pip install -r requirements.txt`

Запуск сервера
`fastapi dev main.py`


ЗАДАНИЕ:
Необходимо создать АПИ для фильмотеки

Основные сущности

    Фильм (Movie)

        Название (обязательное)

        Год выпуска

        Жанры (множественный выбор)

        Продолжительность (мин)

        Рейтинг (0-10)

        Описание(необязательно)

        Постер (URL изображения)

        Дата добавления в систему

    Жанр (Genre)

        Название (обязательное)

        Описание

эндпоинты

    GET /movies - список всех фильмов

    GET /movies/{id} - детальная информация о фильме

    POST /movies - добавление нового фильма

    PUT /movies/{id} - обновление информации о фильме
    PUT /movies/{id}/image - обновление постера фильма

    DELETE /movies/{id} - удаление фильма

    GET /genres - список всех жанров

    POST /genres - добавление нового жанра


Задачи:

    Создать модели для сущностей
    Сделать посев (2-3 фильма и жанра)
    Добавить все эндпоинты
    предусмотреть валидацию данных
    загрузка постера (валидация по типу и размеру, обработать проблему одинаковых имен файлов)

DB SQLite
Пиши на русском языке