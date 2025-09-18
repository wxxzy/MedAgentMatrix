from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.schema import Base
from app.models import nmpa_data # 导入nmpa_data模块以确保其模型被Base.metadata识别
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
