from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings
import os

db_dir = os.path.dirname(f"./{settings.DB_NAME}")
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir) 

DATABASE_URL = f"sqlite:///./{settings.DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} 
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()