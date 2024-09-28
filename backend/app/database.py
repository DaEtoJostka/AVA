from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import cfg

engine = create_engine(cfg.db.uri, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
