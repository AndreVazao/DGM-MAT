from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from shared.config.settings import DB_PATH

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

class Base(DeclarativeBase):
    pass
